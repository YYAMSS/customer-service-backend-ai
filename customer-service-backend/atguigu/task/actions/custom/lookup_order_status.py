from atguigu.task.actions.base import Action, ActionResult
from atguigu.task.actions.custom.shared import _build_order_summary, fetch_order
from atguigu.domain.state import DialogueState


class LookupOrderStatusAction(Action):
    """Fetches order status and summary from the e-commerce service."""

    name = "action_lookup_order_status"

    async def run(self, state: DialogueState, **kwargs: object) -> ActionResult:
        order_number = str(state.get_slot("order_number") or "").strip()
        payload = await fetch_order(order_number)

        if payload is None:
            return ActionResult(slot_updates={
                "order_status": "查询失败",
                "order_summary": "暂时无法查到该订单信息，请稍后再试。",
            })

        return ActionResult(slot_updates={
            "order_status": payload.get("status_desc") or payload.get("status") or "未知",
            "order_summary": _build_order_summary(payload),
        })
