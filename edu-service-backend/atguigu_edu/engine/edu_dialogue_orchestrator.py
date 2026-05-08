from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import httpx
from langchain_core.output_parsers import StrOutputParser

from atguigu_edu.infrastructure.llm import llm
from atguigu_edu.prompts.loader import load_prompt_template

from atguigu_edu.domain.message import BotMessage, Message, MessageObject, MessageType
from atguigu_edu.domain.state import DialogueState
from atguigu_edu.infrastructure.business_provider import BusinessProvider, BusinessProviderError

FLOW_REFUND = "refund"
FLOW_TICKET = "ticket"
FLOW_PROGRESS = "progress"

ORDER_PATTERN = re.compile(r"\b(ORD[A-Z0-9_-]+)\b", re.I | re.ASCII)
COHORT_CODE_PATTERN = re.compile(r"\b(COH[A-Z0-9_-]+)\b", re.I | re.ASCII)
CANCEL_PATTERN = re.compile(r"(取消|算了|不用了|退出流程|结束当前)")
CONFIRM_PATTERN = re.compile(r"(确认提交|^确认$|是的$|好的$|提交$|确定$|可以$)")
RESUME_PATTERN = re.compile(r"(^继续$|^接着$|恢复|继续处理)")
SKIP_OPTIONAL_PATTERN = re.compile(r"(跳过|没有订单|无订单|暂无订单|没有)")


def _fmt_amount(v: Any) -> str:
    if v is None:
        return "-"
    if isinstance(v, Decimal):
        return format(v, "f").rstrip("0").rstrip(".") if "." in format(v, "f") else str(v)
    return str(v)


def _fmt_dt(v: Any) -> str:
    if v is None:
        return "-"
    return str(v)


def extract_order_no(text: str) -> str | None:
    m = ORDER_PATTERN.search(text or "")
    return m.group(1).upper() if m else None


def extract_cohort_code(text: str) -> str | None:
    m = COHORT_CODE_PATTERN.search(text or "")
    return m.group(1).upper() if m else None


def wants_cancel(text: str) -> bool:
    return bool(CANCEL_PATTERN.search(text or ""))


def wants_confirm(text: str) -> bool:
    t = (text or "").strip()
    if len(t) > 40:
        return False
    return bool(CONFIRM_PATTERN.search(t))


def wants_resume(text: str) -> bool:
    t = (text or "").strip()
    return bool(RESUME_PATTERN.search(t))


def _kb_rules_reply(text: str) -> str | None:
    """通用规则 / 使用指南（知识库口径摘要，演示）。对应需求 §3.1.3."""
    t = text or ""
    if any(k in t for k in ("平台规则", "用户协议", "违规处理", "账号封禁")):
        return (
            "【知识库·平台规则（摘要）】请遵守法律法规与课堂秩序：禁止倒卖课程、群发广告、剽窃他人作业。"
            "争议处理以平台公示规则为准，可在「设置-合规中心」查看完整条文。"
        )
    if any(k in t for k in ("怎么用", "怎么使用", "使用指南", "入门", "从哪里开始", "如何使用")):
        return (
            "【知识库·使用指南】建议你：登录后进入「选课中心」选课 → 「我的订单」支付/查看 → 「学习中心」跟课。"
            "若遇到播放或作业问题，可说出「工单」由我协助登记。"
        )
    return None


def _faq_reply(text: str) -> str | None:
    t = text or ""
    if "退款政策" in t or "退款规则" in t or "能退吗" in t:
        return (
            "退款政策（摘要）：开课前可申请全额退款；开课後按课次消耗比例核算。"
            "具体以报名时签署的协议及教务审核为准。如需发起退款，请直接说「我要退款」并按提示提供订单号。"
        )
    if "开课" in t and ("政策" in t or "时间" in t or "什么时候" in t):
        return (
            "开课安排：各班次开结课日期在课程详情与班次信息中展示。"
            "你可发送课程或班次名称，我帮你查在售班次与时间安排。"
        )
    return None


def _progress_keywords(text: str) -> bool:
    t = text or ""
    return any(
        k in t
        for k in (
            "学习进度",
            "学到哪",
            "考勤",
            "作业完成",
            "考试情况",
            "视频看完",
            "进度怎么样",
        )
    )


def _course_keywords(text: str) -> bool:
    t = text or ""
    return any(
        k in t
        for k in (
            "课程",
            "学费",
            "大纲",
            "试听",
            "班型",
            "授课",
            "咨询",
            "多少钱",
            "介绍",
            "培训",
            "怎么学",
            "入门班",
            "进阶班",
            "基础班",
            "提高班",
            "系统班",
            "实战班",
            "训练营",
            "上课",
            "讲课",
            "怎么样",
        )
    )


def _refund_keywords(text: str) -> bool:
    t = text or ""
    return "退款" in t or "退费" in t or "申请退" in t


def _ticket_keywords(text: str) -> bool:
    t = text or ""
    return any(k in t for k in ("工单", "投诉", "售后", "人工客服", "找人工"))


def _order_lookup_keywords(text: str) -> bool:
    t = text or ""
    if extract_order_no(t):
        return True
    return any(k in t for k in ("订单", "查单", "支付", "下单"))


def _pick_cohort(user_text: str, cohorts: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not cohorts:
        return None
    t = (user_text or "").strip()
    best: dict[str, Any] | None = None
    best_score = 0
    for c in cohorts:
        name = str(c.get("cohort_name") or "")
        code = str(c.get("cohort_code") or "")
        score = 0
        if code and code in t:
            score += len(code) + 5
        if name and name in t:
            score += min(len(name), 20)
        for piece in re.split(r"[\s，,、]+", t):
            if len(piece) < 2:
                continue
            if piece in name or piece in code:
                score += len(piece)
        if score > best_score:
            best_score = score
            best = c
    return best if best_score >= 2 else None


def _pick_course(user_text: str, courses: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not courses:
        return None
    t = (user_text or "").strip()
    best: dict[str, Any] | None = None
    best_score = 0
    for c in courses:
        name = str(c.get("series_name") or "")
        code = str(c.get("series_code") or "")
        score = 0
        if code and code in t:
            score += len(code) + 3
        if name and name in t:
            score += min(len(name), 24)
        if name:
            for piece in re.split(r"[\s，,、]+", t):
                if len(piece) < 2:
                    continue
                if piece.lower() in name.lower():
                    score += len(piece)
        if score > best_score:
            best_score = score
            best = c
    return best if best_score >= 2 else None


def _list_lines_course(courses: list[dict[str, Any]], limit: int = 8) -> str:
    lines = []
    for i, c in enumerate(courses[:limit], start=1):
        lines.append(
            f"{i}. {c.get('series_name','')}（代码 {c.get('series_code','')}，状态 {c.get('sale_status','')}）"
        )
    return "\n".join(lines)


def _list_lines_orders(orders: list[dict[str, Any]], limit: int = 8) -> str:
    lines = []
    for i, o in enumerate(orders[:limit], start=1):
        lines.append(
            f"{i}. 订单 {o.get('order_no','')} — {o.get('order_status','')} — ¥{_fmt_amount(o.get('amount'))}"
        )
    return "\n".join(lines)


async def _safe_order(business: BusinessProvider, order_no: str) -> dict[str, Any] | None:
    try:
        return await business.order(order_no)  # type: ignore[return-value]
    except (BusinessProviderError, httpx.HTTPError):
        return None


def _recent_user_texts(state: DialogueState, count: int = 3) -> list[str]:
    """提取最近几轮用户消息文本，用于上下文回查。"""
    texts: list[str] = []
    session = state.current_session()
    if not session:
        return texts
    for turn in reversed(session.turns[-count:]):
        if turn.input_message.text:
            texts.insert(0, turn.input_message.text.strip())
    return texts


# ── 对话历史总结与冲突解决（§3.3 上下文保持）──

_SUMMARIZE_PROMPT = load_prompt_template("intent/summarize_context")
_SUMMARIZE_PARSER = StrOutputParser()


def _build_transcript(state: DialogueState, max_turns: int = 8) -> list[str]:
    """构建对话记录文本行列表。"""
    lines: list[str] = []
    session = state.current_session()
    if not session:
        return lines
    for turn in session.turns[-max_turns:]:
        if turn.input_message.text:
            lines.append(f"用户：{turn.input_message.text.strip()}")
        for am in turn.assistant_messages:
            if am.text:
                lines.append(f"助手：{am.text}")
    return lines


def _parse_summary(raw: str) -> dict[str, str]:
    """解析 LLM 输出的 5 行摘要。"""
    result = {
        "topic": "",
        "course": "",
        "order_no": "",
        "cohort": "",
        "intent": "chitchat",
    }
    for line in raw.strip().split("\n"):
        line = line.strip()
        if line.startswith("当前主题：") or line.startswith("当前主题:"):
            result["topic"] = line.split("：", 1)[-1].split(":", 1)[-1].strip()
        elif line.startswith("涉及课程：") or line.startswith("涉及课程:"):
            val = line.split("：", 1)[-1].split(":", 1)[-1].strip()
            result["course"] = "" if val in ("无", "暂无", "") else val
        elif line.startswith("涉及订单号：") or line.startswith("涉及订单号:"):
            val = line.split("：", 1)[-1].split(":", 1)[-1].strip()
            result["order_no"] = "" if val in ("无", "暂无", "") else val
        elif line.startswith("涉及班次：") or line.startswith("涉及班次:"):
            val = line.split("：", 1)[-1].split(":", 1)[-1].strip()
            result["cohort"] = "" if val in ("无", "暂无", "") else val
        elif line.startswith("用户意图：") or line.startswith("用户意图:"):
            val = line.split("：", 1)[-1].split(":", 1)[-1].strip().lower()
            result["intent"] = val if val in _VALID_INTENTS else "chitchat"
    return result


async def _summarize_context(message: Message, state: DialogueState) -> dict[str, str]:
    """用 LLM 总结最近对话上下文，提取实体、解析冲突（最新优先）、识别意图。"""
    transcript = _build_transcript(state, max_turns=8)

    # 单条消息：用 LLM 意图分类，不做总结
    if len(transcript) <= 1:
        user_text = (message.text or "").strip()
        return {
            "topic": user_text,
            "course": _pick_course_name(user_text),
            "order_no": extract_order_no(user_text) or "",
            "cohort": "",
            "intent": await _classify_intent(message, state),
        }

    try:
        chain = _SUMMARIZE_PROMPT | llm | _SUMMARIZE_PARSER
        raw = (await chain.ainvoke({
            "transcript": transcript,
            "user_message": (message.text or "").strip(),
        })).strip()
        result = _parse_summary(raw)
        if result["topic"]:
            return result
    except Exception:
        logging.getLogger("edu.summary").warning("Context summarization failed", exc_info=True)

    # 降级：规则提取
    user_text = (message.text or "").strip()
    return {
        "topic": user_text,
        "course": _pick_course_name(user_text) or "",
        "order_no": extract_order_no(user_text) or "",
        "cohort": "",
        "intent": _classify_intent_rules(user_text),
    }


def _pick_course_name(text: str) -> str:
    """从文本中检测课程名称（简单规则，供降级用）。"""
    t = (text or "").strip()
    for kw in ("信息学", "编程", "全栈", "Python", "Java", "前端", "后端", "数据分析", "机器学习", "深度学习", "数学", "物理", "化学"):
        if kw in t:
            return kw
    return ""


# ── 保留的旧函数（供降级兼容）──

def _resolve_course_from_history(user_text: str, state: DialogueState, courses: list[dict[str, Any]]) -> dict[str, Any] | None:
    """当前消息无法匹配课程时，从对话历史中查找最近提及的课程。"""
    t = (user_text or "").strip()
    if len(t) <= 6 or any(w in t for w in ("它", "这个", "那个", "多少钱", "价格", "开课", "什么时候", "多久", "怎么学", "如何")):
        for old_text in reversed(_recent_user_texts(state, count=4)):
            picked = _pick_course(old_text, courses)
            if picked:
                return picked
    return None


def _resolve_order_from_history(user_text: str, state: DialogueState) -> str | None:
    """当前消息无法提取订单号时，从对话历史中查找最近提及的订单号。"""
    t = (user_text or "").strip()
    if not extract_order_no(t) and len(t) <= 10:
        for old_text in reversed(_recent_user_texts(state, count=4)):
            on = extract_order_no(old_text)
            if on:
                return on
    return None


async def _reply_course_consultation(sender_id: str, user_text: str, business: BusinessProvider, state: DialogueState | None = None) -> list[BotMessage]:
    try:
        pack = await business.student_courses(sender_id, limit=20)
    except (BusinessProviderError, httpx.HTTPError):
        return [BotMessage(text="课程数据暂时无法获取，请确认业务服务与数据库已启动。")]
    courses = list((pack or {}).get("courses") or [])
    if not courses:
        return [BotMessage(text="当前没有可展示的课程列表，请稍后再试或联系教务。")]
    picked = _pick_course(user_text, courses)
    if not picked and state is not None:
        picked = _resolve_course_from_history(user_text, state, courses)
    if picked:
        code = str(picked.get("series_code") or "")
        try:
            detail = await business.course(code)
        except (BusinessProviderError, httpx.HTTPError):
            detail = picked

        # 查询该课程的班次及价格
        cohort_lines = ""
        try:
            cohort_pack = await business.student_cohorts(sender_id, limit=50)
            all_cohorts = list((cohort_pack or {}).get("cohorts") or [])
            matched_cohorts = [c for c in all_cohorts if str(c.get("series_code") or "") == code]
            if matched_cohorts:
                cohort_lines = "\n".join(
                    f"  {i}. {c.get('cohort_name','')} — ¥{_fmt_amount(c.get('sale_price'))}（{c.get('start_date','')} 开课）"
                    for i, c in enumerate(matched_cohorts[:5], start=1)
                )
        except (BusinessProviderError, httpx.HTTPError):
            pass

        # 用 LLM 生成自然回复
        try:
            detail_text = "\n".join([
                f"课程：{detail.get('series_name', picked.get('series_name'))}",
                f"代码：{detail.get('series_code', code)}",
                f"适用人群：{detail.get('target_audience', '未注明')}",
                f"状态：{detail.get('sale_status', '')}",
                f"方式：{detail.get('delivery_mode', '')}",
                f"描述：{detail.get('description', '')}",
            ])
            if cohort_lines:
                detail_text += f"\n可选班次与价格：\n{cohort_lines}"
            natural = (
                await (load_prompt_template("course/detail_with_price") | llm | StrOutputParser())
                .ainvoke({
                    "user_message": user_text,
                    "course_detail": detail_text,
                })
            ).strip()
            if natural:
                return [BotMessage(text=natural)]
        except Exception:
            pass

        lines = [
            f"【{detail.get('series_name', picked.get('series_name'))}】",
            f"- 课程代码：{detail.get('series_code', code)}",
            f"- 适用人群：{detail.get('target_audience', '以课程详情页说明为准')}",
            f"- 销售状态：{detail.get('sale_status', '')}",
            f"- 授课方式：{detail.get('delivery_mode', '')}",
        ]
        if cohort_lines:
            lines.append(f"\n可选班次与价格：\n{cohort_lines}")
        else:
            lines.append("\n当前暂无对应班次数据，可联系教务了解开课安排。")
        return [BotMessage(text="\n".join(lines))]
    course_list_text = _list_lines_course(courses)
    # Use LLM to generate a natural response with course list as context
    try:
        chain = _INTENT_PROMPT | llm | _INTENT_PARSER  # reuse llm for response generation
        natural_reply = (
            await (load_prompt_template("course/list_with_pricing") | llm | StrOutputParser())
            .ainvoke({
                "user_message": user_text,
                "course_list": course_list_text,
            })
        ).strip()
        if natural_reply:
            return [BotMessage(text=natural_reply)]
    except Exception:
        pass

    return [BotMessage(text="\n".join([
        "你可以直接说出感兴趣的课程名称或方向（例如「Python」「Java」），我会帮你查看课程详情。",
        "价格因班次而异，告诉我你感兴趣的课程，我帮你查具体班次和价格～",
        "",
        "当前可选课程（节选）：",
        course_list_text,
    ]))]


async def _reply_order_lookup(sender_id: str, user_text: str, business: BusinessProvider, state: DialogueState | None = None) -> list[BotMessage]:
    on = extract_order_no(user_text)
    if not on and state is not None:
        on = _resolve_order_from_history(user_text, state)
    if on:
        data = await _safe_order(business, on)
        if not data:
            return [BotMessage(text=f"未找到订单「{on}」。请核对订单号（形如 ORD…），或说明报名手机号协助排查。")]
        lines = [
            f"订单号：{data.get('order_no','')}",
            f"状态：{data.get('order_status','')}",
            f"应付金额：¥{_fmt_amount(data.get('amount'))}",
            f"创建时间：{_fmt_dt(data.get('created_at'))}",
        ]
        if data.get("course_name"):
            lines.insert(2, f"报名课程：{data.get('course_name')}")
        if data.get("paid_at"):
            lines.append(f"支付时间：{_fmt_dt(data.get('paid_at'))}")
        return [BotMessage(text="\n".join(lines))]
    try:
        pack = await business.student_orders(sender_id, limit=15)
    except (BusinessProviderError, httpx.HTTPError):
        return [BotMessage(text="订单列表暂时无法获取。")]
    orders = list((pack or {}).get("orders") or [])
    if not orders:
        return [
            BotMessage(
                text=(
                    "未在示例数据中找到订单记录。请直接发送完整订单号（例如 ORD20240401005），"
                    "或先在教务侧确认订单是否已同步到演示库。"
                )
            )
        ]
    return [
        BotMessage(
            text=(
                "这是与你账号关联的近期订单（演示数据）：\n"
                f"{_list_lines_orders(orders)}\n"
                "若要查看某一单详情，请发送对应订单号。"
            )
        )
    ]


async def _learning_progress_messages(
    sender_id: str, cohort_code: str, business: BusinessProvider, *, ambiguity_note: str | None = None
) -> list[BotMessage]:
    if not cohort_code:
        return [BotMessage(text="未能识别班次代码，请尝试复制班次全称或代码后再问一次。")]
    try:
        prog = await business.cohort_learning_progress(sender_id, cohort_code)
    except (BusinessProviderError, httpx.HTTPError) as e:
        return [BotMessage(text=f"学习进度查询失败：{e}")]
    note = str(prog.get("note") or "").strip()
    lines = [
        f"班次：{prog.get('cohort_name','')}（{prog.get('cohort_code','')}）",
        f"所属课程代码：{prog.get('series_code','')}",
        f"考勤：出勤 {prog.get('attendance_present', 0)} / 计划课次约 {prog.get('attendance_scheduled', 0)}（缺勤 {prog.get('attendance_absent', 0)}）",
        f"视频：完成约 {prog.get('video_completed', 0)} / {prog.get('video_total', 0)}（按课次演示口径）",
        f"作业：提交 {prog.get('homework_submitted', 0)} / {prog.get('homework_total', 0)}",
        f"考试：参加 {prog.get('exam_taken', 0)} / {prog.get('exam_total', 0)}",
    ]
    if ambiguity_note:
        lines.insert(1, ambiguity_note)
    if note:
        lines.append(f"说明：{note}")
    return [BotMessage(text="\n".join(lines))]


async def _reply_learning_progress_for_cohort(
    sender_id: str,
    cohort_code: str,
    user_text_hint: str,
    cohorts: list[dict[str, Any]],
    business: BusinessProvider,
) -> list[BotMessage]:
    del user_text_hint
    del cohorts
    return await _learning_progress_messages(sender_id, cohort_code, business, ambiguity_note=None)


async def _reply_learning_progress(sender_id: str, user_text: str, business: BusinessProvider) -> list[BotMessage]:
    try:
        pack = await business.student_cohorts(sender_id, limit=30)
    except (BusinessProviderError, httpx.HTTPError):
        return [BotMessage(text="班次数据暂时无法获取。")]
    cohorts = list((pack or {}).get("cohorts") or [])
    if not cohorts:
        return [BotMessage(text="暂无班次记录。报名成功后才会展示学习进度相关统计。")]
    picked = _pick_cohort(user_text, cohorts)
    target = picked or cohorts[0]
    code = str(target.get("cohort_code") or "")
    ambiguity_note = None
    if not picked:
        ambiguity_note = (
            "未在消息里匹配到明确班次，为你展示最近一个班次的统计；如需指定班次，请包含班次名称或代码。"
        )
    msgs = await _learning_progress_messages(sender_id, code, business, ambiguity_note=ambiguity_note)
    return msgs


_GREETING_WORDS = {"你好", "嗨", "hi", "hello", "在吗", "嗨喽", "早", "晚上好", "下午好", "hey", "哈喽", "哈啰"}

def _ambiguous_user_intent(text: str) -> bool:
    """检测是否为真正模糊/不明确的输入（问候等不算模糊，应走闲聊 LLM）。"""
    t = (text or "").strip()
    # 常见问候不是模糊意图，交给 LLM 闲聊处理
    if t.lower() in _GREETING_WORDS:
        return False
    if len(t) <= 2:
        return True
    if t in {"帮我一下", "帮帮我", "怎么办"}:
        return True
    if "退款" in t and "投诉" in t:
        return True
    return False


def _flow_prompt(state: DialogueState) -> str:
    if state.active_flow == FLOW_REFUND:
        step = state.flow_step or ""
        if step == "collect_order":
            return "请先提供要退款的订单号（形如 ORD…），或从页面发送订单对象。"
        if step == "collect_reason":
            return "请简要说明退款原因（例如：时间冲突、重复购买等）。"
        if step == "collect_refund_type":
            return "请选择退款类型：回复「全额」或「部分」。若不确定可直接回复「全额」。"
        if step == "confirm":
            return "请核对上方信息，确认无误后回复「确认」提交退款申请。"
    if state.active_flow == FLOW_TICKET:
        step = state.flow_step or ""
        if step == "collect_ticket_type":
            return "请选择工单类型：售后 / 投诉 / 退款问题 / 建议 —— 直接回复其中一类。"
        if step == "collect_order":
            return "请提供关联订单号；如无订单可回复「跳过」。"
        if step == "collect_description":
            return "请详细描述问题现象与期望处理结果（一条消息内尽量写全）。"
        if step == "confirm":
            return "请回复「确认」创建工单。"
    if state.active_flow == FLOW_PROGRESS:
        if (state.flow_step or "") == "collect_cohort":
            return "请回复班次名称或班次代码（如 COH…），我好查询该班次的学习进度。"
    return ""


async def _handle_progress_flow(sender_id: str, text: str, state: DialogueState, business: BusinessProvider) -> list[BotMessage]:
    enriched = extract_cohort_code(text) or text
    try:
        pack = await business.student_cohorts(sender_id, limit=50)
    except (BusinessProviderError, httpx.HTTPError):
        return [BotMessage(text="班次数据暂时无法获取，请稍后再试。")]
    cohorts = list((pack or {}).get("cohorts") or [])
    if not cohorts:
        state.clear_flow()
        return [BotMessage(text="暂无班次记录。")]
    picked = _pick_cohort(enriched, cohorts)
    if not picked:
        return [BotMessage(text="未匹配到班次，请提供更完整的班次全称或班次代码（如 COH…）。")]
    state.clear_flow()
    return await _reply_learning_progress_for_cohort(
        sender_id, str(picked.get("cohort_code") or ""), enriched, cohorts, business
    )


async def _handle_flow_text(message: Message, state: DialogueState, business: BusinessProvider) -> list[BotMessage] | None:
    if message.type is not MessageType.TEXT:
        return None
    text = (message.text or "").strip()
    if not state.active_flow:
        return None

    if state.active_flow == FLOW_REFUND:
        return await _handle_refund_flow(text, state, business)
    if state.active_flow == FLOW_TICKET:
        return await _handle_ticket_flow(text, state, business)
    if state.active_flow == FLOW_PROGRESS:
        return await _handle_progress_flow(message.sender_id, text, state, business)
    return None


async def _handle_refund_flow(text: str, state: DialogueState, business: BusinessProvider) -> list[BotMessage]:
    step = state.flow_step or "collect_order"
    if step != "collect_order":
        other = extract_order_no(text)
        prev = state.flow_slots.get("order_no")
        if prev and other and other != prev.upper():
            return [
                BotMessage(
                    text=(
                        f"你先前提供的订单号是 {prev}，当前消息里出现了 {other}，两者不一致。\n"
                        "请直接回复要继续处理的那一单订单号或说「取消」重置流程。"
                    )
                )
            ]
    if step == "collect_order":
        on = extract_order_no(text)
        if not on:
            return [BotMessage(text="没有识别到订单号，请发送类似 ORD20240401005 的订单号。")]
        data = await _safe_order(business, on)
        if not data:
            return [BotMessage(text=f"订单「{on}」不存在或暂不可查，请核对后再发。")]
        state.flow_slots["order_no"] = on
        state.flow_slots["order_status"] = str(data.get("order_status") or "")
        state.flow_step = "collect_reason"
        return [
            BotMessage(
                text=(
                    f"已关联订单 {on}（状态：{state.flow_slots.get('order_status','')}）。\n"
                    "请说明退款原因（一段话即可）。"
                )
            )
        ]
    if step == "collect_reason":
        if len(text) < 2:
            return [BotMessage(text="原因稍短，请补充至少几个字说明退款原因。")]
        state.flow_slots["reason"] = text
        state.flow_step = "collect_refund_type"
        return [
            BotMessage(text="已记录原因。请选择「全额」或「部分」退款；也可直接回复「全额」。"),
        ]
    if step == "collect_refund_type":
        rt = "部分" if "部分" in text else "全额"
        state.flow_slots["refund_type"] = rt
        state.flow_step = "confirm"
        summary = (
            f"请确认退款申请：\n"
            f"- 订单号：{state.flow_slots.get('order_no','')}\n"
            f"- 原因：{state.flow_slots.get('reason','')}\n"
            f"- 类型：{state.flow_slots.get('refund_type','')}\n"
            f"确认请回复「确认」，取消请说「取消」。"
        )
        return [BotMessage(text=summary)]
    if step == "confirm":
        if wants_confirm(text):
            rid = f"REFUND-{uuid.uuid4().hex[:10].upper()}"
            state.clear_flow()
            return [
                BotMessage(
                    text=(
                        f"退款申请已受理，受理编号：{rid}。\n"
                        "教务将在工作日核对订单与协议后处理，请留意短信/站内通知。"
                    )
                )
            ]
        return [BotMessage(text="尚未确认。若信息有误请说「取消」后重新开始；确认请回复「确认」。")]
    return [BotMessage(text=_flow_prompt(state))]


async def _handle_ticket_flow(text: str, state: DialogueState, business: BusinessProvider) -> list[BotMessage]:
    step = state.flow_step or "collect_ticket_type"
    if step == "collect_ticket_type":
        if len(text) < 2:
            return [BotMessage(text="请从「售后 / 投诉 / 退款问题 / 建议」中选一类说明。")]
        state.flow_slots["ticket_type"] = text[:32]
        state.flow_step = "collect_order"
        return [BotMessage(text="请提供关联订单号；如无需关联请回复「跳过」。")]
    if step == "collect_order":
        if SKIP_OPTIONAL_PATTERN.search(text):
            state.flow_slots["order_no"] = ""
        else:
            on = extract_order_no(text)
            if not on:
                return [BotMessage(text="未识别订单号。请发订单号，或回复「跳过」。")]
            data = await _safe_order(business, on)
            if not data:
                return [BotMessage(text="订单不存在，请核对订单号或选择跳过。")]
            state.flow_slots["order_no"] = on
        state.flow_step = "collect_description"
        return [BotMessage(text="请用一段话描述问题（现象、时间、期望处理方式）。")]
    if step == "collect_description":
        if len(text) < 4:
            return [BotMessage(text="描述稍短，请补充更多细节，便于同学定位问题。")]
        state.flow_slots["description"] = text
        state.flow_step = "confirm"
        od = state.flow_slots.get("order_no") or "（未关联）"
        summary = (
            f"即将创建工单：\n"
            f"- 类型：{state.flow_slots.get('ticket_type','')}\n"
            f"- 订单：{od}\n"
            f"- 描述：{state.flow_slots.get('description','')}\n"
            f"确认请回复「确认」。"
        )
        return [BotMessage(text=summary)]
    if step == "confirm":
        if wants_confirm(text):
            tid = f"TICKET-{uuid.uuid4().hex[:10].upper()}"
            slots_snapshot = dict(state.flow_slots)
            state.clear_flow()
            logging.getLogger("edu.audit").info("ticket_created ticket_id=%s slots=%s", tid, slots_snapshot)
            return [
                BotMessage(
                    text=(
                        f"工单已创建，编号：{tid}。\n"
                        "客服将在 1 个工作日内响应；紧急情况请补充手机号以便回访。"
                    )
                )
            ]
        return [BotMessage(text="如需修改请说「取消」；确认请回复「确认」。")]
    return [BotMessage(text=_flow_prompt(state))]


def _maybe_suspend_for_interrupt(state: DialogueState, text: str) -> bool:
    """任务进行中，用户发起订单查询 / 显式新意图时暂存当前任务。"""
    if not state.active_flow:
        return False
    step = state.flow_step or ""
    # 正在填写订单号时，不要把订单号当成「打断」
    if state.active_flow == FLOW_REFUND and step == "collect_order":
        return False
    if state.active_flow == FLOW_TICKET and step == "collect_order":
        return False
    if extract_order_no(text):
        state.suspend_current_flow()
        return True
    if _order_lookup_keywords(text) and not wants_cancel(text):
        state.suspend_current_flow()
        return True
    if _refund_keywords(text) and state.active_flow != FLOW_REFUND:
        state.suspend_current_flow()
        return True
    if _ticket_keywords(text) and state.active_flow != FLOW_TICKET:
        state.suspend_current_flow()
        return True
    return False


async def _handle_object_message(message: Message, state: DialogueState, business: BusinessProvider) -> list[BotMessage]:
    obj = message.object
    assert obj is not None
    if state.active_flow == FLOW_REFUND and (state.flow_step or "") == "collect_order":
        if obj.type.lower() in ("order", "订单"):
            fake_text = obj.id
            return await _handle_refund_flow(fake_text, state, business)
    if state.active_flow == FLOW_TICKET and (state.flow_step or "") == "collect_order":
        if obj.type.lower() in ("order", "订单"):
            fake_text = obj.id
            return await _handle_ticket_flow(fake_text, state, business)
    if state.active_flow == FLOW_PROGRESS and (state.flow_step or "") == "collect_cohort":
        if obj.type.lower() in ("cohort", "班次", "班级"):
            return await _handle_progress_flow(message.sender_id, obj.id, state, business)

    type_zh = "订单" if obj.type.lower() in ("order", "订单") else obj.type
    return [
        BotMessage(
            text=(
                f"已收到你发送的{type_zh}对象（ID：{obj.id}）。\n"
                "需要我帮你：查询该订单详情、匹配课程/班次咨询，还是进入退款/工单流程？直接说需求即可。"
            )
        )
    ]


# ── LLM 意图分类（优先） + 关键词规则（降级）──

_INTENT_PROMPT = load_prompt_template("intent/classify")
_INTENT_PARSER = StrOutputParser()

_VALID_INTENTS = {"course", "order", "progress", "refund", "ticket", "faq", "knowledge", "chitchat"}


async def _classify_intent(message: Message, state: DialogueState) -> str:
    """使用 LLM 分类意图，失败时降级到关键词规则。"""

    async def _llm_classify() -> str:
        chain = _INTENT_PROMPT | llm | _INTENT_PARSER
        history = ""
        session = state.current_session()
        if session and session.turns:
            recent = session.turns[-2:]
            lines = []
            for turn in recent:
                lines.append(f"用户：{turn.input_message.text or ''}")
                for am in turn.assistant_messages:
                    if am.text:
                        lines.append(f"助手：{am.text}")
            history = "\n".join(lines)
        result = await chain.ainvoke({
            "history": history,
            "user_message": (message.text or "").strip(),
        })
        return result.strip().lower()

    try:
        label = (await _llm_classify()).strip()
        if label in _VALID_INTENTS:
            return label
    except Exception:
        logging.getLogger("edu.intent").warning("LLM intent classification failed, using rules", exc_info=True)

    return _classify_intent_rules((message.text or "").strip())


def _classify_intent_rules(text: str) -> str:
    """关键词规则意图分类，作为 LLM 的降级方案。"""
    t = text or ""

    if extract_order_no(t):
        return "order"

    # 多关键词显式匹配
    if _refund_keywords(t) and _ticket_keywords(t):
        return "ticket"

    # 课程优先于 KB（"入门班"中的"入门"不应触发 KB 规则）
    if _course_keywords(t):
        return "course"

    if _progress_keywords(t):
        return "progress"

    if _faq_reply(t):
        return "faq"

    if _kb_rules_reply(t):
        return "knowledge"

    if _order_lookup_keywords(t) and not _progress_keywords(t) and not _refund_keywords(t) and not _ticket_keywords(t):
        return "order"

    if _refund_keywords(t):
        return "refund"

    if _ticket_keywords(t):
        return "ticket"

    return "chitchat"


# ── 闲聊兜底（§3.4）：LLM 生成自然友好回复 + 硬编码降级兜底 ──

_CHITCHAT_PROMPT = load_prompt_template("chitchat/response")
_CHITCHAT_OUTPUT_PARSER = StrOutputParser()

_FALLBACK_TEXT = (
    "我是教育智能客服，主要帮你处理以下事情：\n"
    "📚 课程与班次咨询\n"
    "📋 订单状态查询\n"
    "📊 学习进度查询\n"
    "💡 退款申请与工单提交\n"
    "你可以直接说「我要查订单 ORD…」「Python 课程怎么样」「学习进度」或「我要退款」，我会马上帮你处理～"
)


async def _llm_chitchat_reply(message: Message, state: DialogueState) -> list[BotMessage]:
    """使用 LLM 生成自然友好的闲聊回复，失败时降级到硬编码兜底。"""

    async def _do_llm() -> str:
        chain = _CHITCHAT_PROMPT | llm | _CHITCHAT_OUTPUT_PARSER
        history = ""
        session = state.current_session()
        if session and session.turns:
            recent = session.turns[-3:]
            lines = []
            for turn in recent:
                lines.append(f"用户：{turn.input_message.text or ''}")
                for am in turn.assistant_messages:
                    if am.text:
                        lines.append(f"助手：{am.text}")
            history = "\n".join(lines)
        now = datetime.now(timezone.utc).astimezone()
        return await chain.ainvoke({
            "current_datetime": now.strftime("%Y年%m月%d日 %H:%M %A"),
            "history": history,
            "user_message": (message.text or "").strip(),
        })

    try:
        llm_text = (await _do_llm()).strip()
        if llm_text:
            return [BotMessage(text=llm_text)]
    except Exception:
        logging.getLogger("edu.chitchat").warning("LLM chitchat failed, using fallback", exc_info=True)

    return [BotMessage(text=_FALLBACK_TEXT)]


async def _implicit_course_detail(
    sender_id: str, user_text: str, business: BusinessProvider
) -> list[BotMessage] | None:
    """未出现明显业务关键词时，尝试用课程名/代码模糊匹配。"""
    try:
        pack = await business.student_courses(sender_id, limit=30)
    except (BusinessProviderError, httpx.HTTPError):
        return None
    courses = list((pack or {}).get("courses") or [])
    picked = _pick_course(user_text, courses)
    if not picked:
        return None
    code = str(picked.get("series_code") or "")
    try:
        detail = await business.course(code)
    except (BusinessProviderError, httpx.HTTPError):
        detail = picked
    lines = [
        f"【{detail.get('series_name', picked.get('series_name'))}】",
        f"- 课程代码：{detail.get('series_code', code)}",
        f"- 适用人群：{detail.get('target_audience', '以课程详情页说明为准。')}",
        f"- 销售状态：{detail.get('sale_status', '')}",
        f"- 授课方式：{detail.get('delivery_mode', '')}",
        "需要班次与开课时间可再说一下方向或期数，我帮你缩小范围。",
    ]
    return [BotMessage(text="\n".join(lines))]


async def generate_edu_reply(message: Message, state: DialogueState, business: BusinessProvider) -> list[BotMessage]:
    """根据业务 API 与对话状态生成回复（实现需求说明 3.x 的基础闭环）。"""
    if message.type is MessageType.TEXT:
        raw = (message.text or "").strip()
        if wants_cancel(raw):
            if state.active_flow:
                state.clear_flow()
                msgs: list[BotMessage] = [BotMessage(text="好的，已取消当前流程。")]
                if state.suspended_flow:
                    msgs.append(BotMessage(text="你还有一个暂停中的任务，回复「继续」可接着处理。"))
                return msgs
            if state.suspended_flow:
                state.suspended_flow = None
                return [BotMessage(text="已清除暂停任务记录。")]

        if wants_resume(raw) and not state.active_flow and state.restore_suspended():
            return [
                BotMessage(
                    text=(
                        "已从暂停点恢复当前任务。\n"
                        f"{_flow_prompt(state) or '请根据上一步系统提示继续补充信息。'}"
                    )
                )
            ]

    if message.type is MessageType.OBJECT:
        return await _handle_object_message(message, state, business)

    user_text = (message.text or "").strip()
    if not user_text:
        return [BotMessage(text="请用文字说明你的问题，或发送课程/订单等业务对象。")]

    if _ambiguous_user_intent(user_text) and not state.active_flow:
        hint = (
            "当前描述可能同时涉及多种办理方式。请说明你更需要：订单查询 / 学习进度 / 课程咨询 / 退款申请 / 工单。"
            "也可以直接复述完整需求（附上订单号或班次更好）。"
        )
        return [BotMessage(text=hint)]

    _maybe_suspend_for_interrupt(state, user_text)
    flow_msgs = await _handle_flow_text(message, state, business)
    if flow_msgs is not None:
        return flow_msgs

    # ── 对话上下文总结（实体提取 + 冲突解决 + 意图分类）→ 路由到对应处理器 ──
    ctx = await _summarize_context(message, state)
    intent = ctx["intent"]

    if intent == "faq":
        faq = _faq_reply(user_text)
        if faq:
            return [BotMessage(text=faq)]

    if intent == "knowledge":
        kb = _kb_rules_reply(user_text)
        if kb:
            return [BotMessage(text=kb)]

    if intent == "order":
        msgs = await _reply_order_lookup(message.sender_id, user_text, business, state)
        if state.suspended_flow:
            msgs.append(BotMessage(text="你仍有暂停中的表单流程，回复「继续」可回去填写。"))
        return msgs

    if intent == "progress":
        try:
            pack = await business.student_cohorts(message.sender_id, limit=40)
        except (BusinessProviderError, httpx.HTTPError):
            return [BotMessage(text="班次数据暂时无法获取。")]
        cohorts = list((pack or {}).get("cohorts") or [])
        if not cohorts:
            return [BotMessage(text="暂无班次记录。报名成功后才会展示学习进度相关统计。")]
        if len(cohorts) > 1 and _pick_cohort(user_text, cohorts) is None:
            state.active_flow = FLOW_PROGRESS
            state.flow_step = "collect_cohort"
            state.flow_slots.clear()
            preview = "\n".join(
                f"- {c.get('cohort_name') or '（未命名）'}（{c.get('cohort_code') or ''}）"
                for c in cohorts[:10]
            )
            return [
                BotMessage(
                    text=(
                        "你在多个班次中学习，请指定要查询进度的班次（名称或代码均可）：\n"
                        f"{preview}\n"
                        "也可发送「班次」业务对象。"
                    )
                )
            ]
        msgs = await _reply_learning_progress(message.sender_id, user_text, business)
        if state.suspended_flow:
            msgs.append(BotMessage(text="提示：若有未完成任务，可回复「继续」。"))
        return msgs

    if intent == "course":
        # 用总结出的课程名增强查询
        enriched_text = user_text
        if ctx["course"] and ctx["course"] not in enriched_text:
            enriched_text = f"{ctx['course']} {enriched_text}"
        return await _reply_course_consultation(message.sender_id, enriched_text, business, state)

    if intent == "refund":
        # 从上下文总结或历史中提取订单号，预填槽位
        historic_order = ctx.get("order_no") or _resolve_order_from_history(user_text, state)
        if historic_order:
            data = await _safe_order(business, historic_order)
            state.active_flow = FLOW_REFUND
            state.flow_step = "collect_reason" if data else "collect_order"
            state.flow_slots.clear()
            state.flow_slots["order_no"] = historic_order
            if data:
                state.flow_slots["order_status"] = str(data.get("order_status") or "")
                return [
                    BotMessage(
                        text=(
                            f"已关联你刚才提到的订单 {historic_order}（状态：{state.flow_slots.get('order_status','')}）。\n"
                            "请说明退款原因（一段话即可）。"
                        )
                    )
                ]
            else:
                return [
                    BotMessage(
                        text=(
                            f"已识别到你之前提到的订单号 {historic_order}，但该订单暂未在系统中查到。\n"
                            "请核对订单号后重新发送，或直接回复正确的订单号。"
                        )
                    )
                ]
        state.active_flow = FLOW_REFUND
        state.flow_step = "collect_order"
        state.flow_slots.clear()
        return [
            BotMessage(
                text=(
                    "好的，我来协助你发起退款申请。\n"
                    "第一步：请提供需要退款的订单号（形如 ORD…），也可从调试页发送订单对象。"
                )
            )
        ]

    if intent == "ticket":
        state.active_flow = FLOW_TICKET
        state.flow_step = "collect_ticket_type"
        state.flow_slots.clear()
        # 预填上下文中的订单号
        historic_order = ctx.get("order_no") or _resolve_order_from_history(user_text, state)
        if historic_order:
            data = await _safe_order(business, historic_order)
            if data:
                state.flow_slots["order_no"] = historic_order
        return [
            BotMessage(
                text=(
                    "我来帮你创建工单。\n"
                    "请先说明工单类型：售后 / 投诉 / 退款问题 / 建议（直接回复其中一类）。"
                )
            )
        ]

    # intent == "chitchat" or unknown
    return await _llm_chitchat_reply(message, state)


def infer_intent_for_trace(message: Message, state: DialogueState) -> str:
    """单次请求意图标签（可观测性/测试），与路由分支大致对应。"""
    if message.type is MessageType.OBJECT:
        return "object_submit"
    if state.active_flow == FLOW_REFUND:
        return "task_refund"
    if state.active_flow == FLOW_TICKET:
        return "task_ticket"
    if state.active_flow == FLOW_PROGRESS:
        return "task_progress"
    t = (message.text or "").strip()
    if _faq_reply(t):
        return "faq"
    if _kb_rules_reply(t):
        return "knowledge"
    if extract_order_no(t) or (_order_lookup_keywords(t) and not _progress_keywords(t)):
        return "order_lookup"
    if _progress_keywords(t):
        return "learning_progress"
    if _course_keywords(t):
        return "course_consultation"
    if _refund_keywords(t):
        return "refund_intake"
    if _ticket_keywords(t):
        return "ticket_intake"
    return "chitchat_or_implicit"
