<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'

const senderId = ref('student_001')
const draftMessage = ref('')
const isSending = ref(false)
const errorMessage = ref('')
const messages = ref([])
const messagesContainer = ref(null)

const courses = ref([])
const classes = ref([])
const orders = ref([])
const isLoadingSidebar = ref(false)
const sidebarError = ref('')
const activeTab = ref('courses')

const chatEndpoint = computed(() => '/api/chat')
const chatHistoryEndpoint = computed(
  () => `/api/chat/history?sender_id=${encodeURIComponent(senderId.value.trim())}`,
)
const eduEndpointBase = computed(() => '/edu')

async function fetchEduJson(path) {
  const response = await fetch(`${eduEndpointBase.value}${path}`)
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(payload?.detail || payload?.message || '教育业务服务请求失败。')
  }
  if (payload?.code !== 0) {
    throw new Error(payload?.message || '教育业务服务返回错误。')
  }
  return payload?.data
}

function createBaseMessage(role) {
  return {
    id: crypto.randomUUID(),
    role,
    buttons: [],
  }
}

function appendUserText(text) {
  messages.value.push({
    ...createBaseMessage('user'),
    type: 'text',
    text,
  })
}

function appendUserObject(objectType, payload) {
  messages.value.push({
    ...createBaseMessage('user'),
    type: 'object',
    objectType,
    payload,
  })
}

function appendBotMessages(botMessages) {
  for (const message of botMessages) {
    appendMessage('bot', message)
  }
}

function appendMessage(role, message) {
  if (role === 'divider') {
    messages.value.push({
      ...createBaseMessage('divider'),
      type: 'divider',
      text: message.text ?? '以上为历史消息',
    })
    return
  }

  if (message.object) {
    messages.value.push({
      ...createBaseMessage(role),
      type: 'object',
      objectType: message.object.type,
      payload: message.object,
    })
  } else {
    messages.value.push({
      ...createBaseMessage(role),
      type: 'text',
      text: message.text ?? '',
    })
  }
}

function setHistoryMessages(historyMessages) {
  messages.value = []
  for (const message of historyMessages) {
    const role = ['user', 'bot', 'divider'].includes(message.role) ? message.role : 'bot'
    appendMessage(role, message)
  }
}

async function scrollToBottom() {
  await nextTick()
  const container = messagesContainer.value
  if (!container) {
    return
  }
  container.scrollTop = container.scrollHeight
}

watch(
  () => messages.value.length,
  async () => {
    await scrollToBottom()
  },
)

function resetConversation() {
  messages.value = []
  errorMessage.value = ''
}

function formatAmount(amount) {
  const numericAmount = Number(amount)
  if (Number.isNaN(numericAmount)) {
    return '￥0.00'
  }
  return `￥${numericAmount.toFixed(2)}`
}

function getObjectBadgeLabel(objectType) {
  if (objectType === 'order') {
    return '订单'
  }
  if (objectType === 'course') {
    return '课程'
  }
  if (objectType === 'class') {
    return '班次'
  }
  return '业务对象'
}

function getObjectTitle(message) {
  const payload = message.payload ?? {}
  if (payload.title) {
    return payload.title
  }
  return getObjectBadgeLabel(message.objectType)
}

function getObjectIdentifier(message) {
  const payload = message.payload ?? {}
  const type = message.objectType
  const id =
    payload.id ??
    payload.order_id ??
    payload.course_id ??
    payload.class_id
  if (type === 'order') {
    return id ? `订单号：${id}` : '订单号'
  }
  if (type === 'course') {
    return id ? `课程编码：${id}` : '课程编码'
  }
  if (type === 'class') {
    return id ? `班次编码：${id}` : '班次编码'
  }
  return id ? `ID：${id}` : ''
}

function getObjectSummary(message) {
  const payload = message.payload ?? {}
  const attrs = payload.attributes ?? {}
  if (message.objectType === 'order') {
    const status = payload.status ?? attrs.status
    return status ? `订单状态：${status}` : '订单'
  }
  if (message.objectType === 'course') {
    return payload.description || attrs.description || '课程咨询'
  }
  if (message.objectType === 'class') {
    return payload.schedule || attrs.schedule || '学习进度 / 开班信息'
  }
  return ''
}

function getObjectAmount(message) {
  const payload = message.payload ?? {}
  const attrs = payload.attributes ?? {}
  if (message.objectType === 'order') {
    return formatAmount(payload.amount ?? attrs.amount)
  }
  return ''
}

async function fetchSidebarData() {
  const currentSenderId = senderId.value.trim()
  courses.value = []
  classes.value = []
  orders.value = []
  sidebarError.value = ''

  if (!currentSenderId) {
    return
  }

  isLoadingSidebar.value = true
  try {
    const [courseData, cohortData, orderData] = await Promise.all([
      fetchEduJson(`/students/${encodeURIComponent(currentSenderId)}/courses?limit=10`),
      fetchEduJson(`/students/${encodeURIComponent(currentSenderId)}/cohorts?limit=10`),
      fetchEduJson(`/students/${encodeURIComponent(currentSenderId)}/orders?limit=10`),
    ])
    courses.value = Array.isArray(courseData?.courses) ? courseData.courses : []
    classes.value = Array.isArray(cohortData?.cohorts) ? cohortData.cohorts : []
    orders.value = Array.isArray(orderData?.orders) ? orderData.orders : []
  } catch (error) {
    sidebarError.value = error instanceof Error ? error.message : '加载业务对象失败。'
  } finally {
    isLoadingSidebar.value = false
  }
}

async function fetchChatHistory() {
  const currentSenderId = senderId.value.trim()
  if (!currentSenderId) {
    messages.value = []
    return
  }

  try {
    const response = await fetch(chatHistoryEndpoint.value)
    const data = await response.json()
    if (!response.ok) {
      throw new Error(data.detail || '加载历史消息失败。')
    }
    if (currentSenderId === senderId.value.trim()) {
      setHistoryMessages(Array.isArray(data?.messages) ? data.messages : [])
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载历史消息失败。'
  }
}

async function sendPayload(payload) {
  if (isSending.value) {
    return
  }

  errorMessage.value = ''
  isSending.value = true

  try {
    const response = await fetch(chatEndpoint.value, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sender_id: senderId.value.trim(),
        ...payload,
      }),
    })

    const data = await response.json()
    if (!response.ok) {
      throw new Error(data.detail || '请求失败。')
    }

    appendBotMessages(data.messages ?? [])
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '请求失败。'
  } finally {
    isSending.value = false
  }
}

async function sendTextMessage() {
  const text = draftMessage.value.trim()
  const currentSenderId = senderId.value.trim()

  if (!currentSenderId) {
    errorMessage.value = '请先填写学员标识（sender_id）。'
    return
  }
  if (!text) {
    return
  }

  draftMessage.value = ''
  appendUserText(text)
  await sendPayload({ text })
}

async function sendCourse(course) {
  const currentSenderId = senderId.value.trim()
  if (!currentSenderId) {
    errorMessage.value = '请先填写学员标识（sender_id）。'
    return
  }

  appendUserObject('course', course)
  await sendPayload({
    object: {
      type: 'course',
      id: course.series_code,
      title: course.series_name,
      attributes: {
        sale_status: course.sale_status,
        delivery_mode: course.delivery_mode,
      },
    },
  })
}

async function sendClass(cls) {
  const currentSenderId = senderId.value.trim()
  if (!currentSenderId) {
    errorMessage.value = '请先填写学员标识（sender_id）。'
    return
  }

  appendUserObject('class', cls)
  await sendPayload({
    object: {
      type: 'class',
      id: cls.cohort_code,
      title: cls.cohort_name,
      attributes: {
        series_code: cls.series_code,
        sale_price: cls.sale_price,
        start_date: cls.start_date,
        end_date: cls.end_date,
      },
    },
  })
}

async function sendOrder(order) {
  const currentSenderId = senderId.value.trim()
  if (!currentSenderId) {
    errorMessage.value = '请先填写学员标识（sender_id）。'
    return
  }

  appendUserObject('order', order)
  await sendPayload({
    object: {
      type: 'order',
      id: order.order_no,
      title: `订单 ${order.order_no}`,
      attributes: {
        status: order.order_status,
        status_desc: order.status_desc,
        amount: order.amount,
        created_at: order.created_at,
      },
    },
  })
}

watch(
  () => senderId.value.trim(),
  async (value, previousValue) => {
    if (value === previousValue) {
      return
    }

    resetConversation()
    if (!value) {
      courses.value = []
      classes.value = []
      orders.value = []
      return
    }
    await Promise.all([fetchSidebarData(), fetchChatHistory()])
  },
)

onMounted(async () => {
  await Promise.all([fetchSidebarData(), fetchChatHistory()])
})
</script>

<template>
  <div class="app-shell">
    <header class="top-bar">
      <div class="brand">
        <span class="brand-icon" aria-hidden="true">📚</span>
        <div class="brand-text">
          <div class="brand-title">教育智能客服</div>
          <div class="brand-sub">课程咨询 · 订单查询 · 学习进度 · 在线办理</div>
        </div>
      </div>
      <div class="top-meta">
        <span class="pill">调试页</span>
        <span v-if="senderId.trim()" class="sender-pill"
          >当前学员：<strong>{{ senderId.trim() }}</strong></span
        >
      </div>
    </header>

    <div class="workspace">
      <div class="chat-card">
        <div class="chat-inner-header">
          <h1>对话</h1>
          <p class="muted">与智能客服对话，或从右侧发送课程 / 班次 / 订单对象。</p>
        </div>

        <section class="controls">
          <label class="field">
            <span>学员标识 sender_id</span>
            <div class="field-row">
              <input v-model="senderId" type="text" placeholder="student_001" />
              <button
                type="button"
                class="secondary-button"
                :disabled="isLoadingSidebar"
                @click="fetchSidebarData"
              >
                {{ isLoadingSidebar ? '加载中…' : '刷新对象列表' }}
              </button>
            </div>
          </label>
        </section>

        <section ref="messagesContainer" class="messages">
          <div v-if="messages.length === 0" class="empty-state">
            你可以直接输入问题，例如「<code>我想了解 Python 课程</code>」「<code>查一下我的订单</code>」，
            或在右侧点击课程、班次、订单，将结构化对象发送给后端。
          </div>

          <article
            v-for="message in messages"
            :key="message.id"
            class="message"
            :class="message.role"
          >
            <template v-if="message.type === 'divider'">
              <div class="history-divider">
                <span>{{ message.text }}</span>
              </div>
            </template>

            <template v-else>
              <div class="meta">
                {{
                  message.role === 'user' ? '学员' : message.role === 'bot' ? '智能客服' : ''
                }}
              </div>

              <div class="bubble">
                <template v-if="message.type === 'object'">
                  <div
                    class="object-card"
                    :class="`object-card-${message.objectType || 'unknown'}`"
                  >
                    <div class="object-card-badge">
                      {{ getObjectBadgeLabel(message.objectType) }}
                    </div>
                    <div class="object-card-title">{{ getObjectTitle(message) }}</div>
                    <div class="object-card-meta">{{ getObjectIdentifier(message) }}</div>
                    <div class="object-card-meta">{{ getObjectSummary(message) }}</div>
                    <div v-if="message.objectType === 'order'" class="object-card-price">
                      {{ getObjectAmount(message) }}
                    </div>
                  </div>
                </template>

                <template v-else>
                  <p>{{ message.text }}</p>
                </template>
              </div>
            </template>
          </article>
        </section>

        <p v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </p>

        <form class="composer" @submit.prevent="sendTextMessage">
          <input
            v-model="draftMessage"
            type="text"
            placeholder="输入咨询内容，回车或点击发送…"
            :disabled="isSending"
          />
          <button type="submit" :disabled="isSending || !draftMessage.trim()">
            {{ isSending ? '发送中…' : '发送' }}
          </button>
        </form>
      </div>

      <aside class="sidebar">
        <div class="sidebar-header">
          <h2>业务对象</h2>
          <p class="muted small">数据来自教育业务服务（edu-service-backend-business）。</p>
        </div>

        <div class="tabs">
          <button
            type="button"
            class="tab-button"
            :class="{ active: activeTab === 'courses' }"
            @click="activeTab = 'courses'"
          >
            课程
          </button>
          <button
            type="button"
            class="tab-button"
            :class="{ active: activeTab === 'classes' }"
            @click="activeTab = 'classes'"
          >
            班次
          </button>
          <button
            type="button"
            class="tab-button"
            :class="{ active: activeTab === 'orders' }"
            @click="activeTab = 'orders'"
          >
            订单
          </button>
        </div>

        <p v-if="sidebarError" class="sidebar-error">{{ sidebarError }}</p>

        <div v-if="activeTab === 'courses'" class="sidebar-list">
          <div v-if="!courses.length && !isLoadingSidebar" class="sidebar-empty">
            暂无课程数据
          </div>

          <article v-for="c in courses" :key="c.series_code" class="sidebar-card">
            <div class="card-top">
              <div class="card-title">{{ c.series_name }}</div>
            </div>
            <div class="card-meta">售卖状态：{{ c.sale_status }}</div>
            <div class="card-meta">交付方式：{{ c.delivery_mode }}</div>
            <div class="card-meta">课程编码：{{ c.series_code }}</div>
            <button
              type="button"
              class="primary-outline full-width"
              :disabled="isSending"
              @click="sendCourse(c)"
            >
              发送课程对象
            </button>
          </article>
        </div>

        <div v-else-if="activeTab === 'classes'" class="sidebar-list">
          <div v-if="!classes.length && !isLoadingSidebar" class="sidebar-empty">
            暂无班次数据
          </div>

          <article v-for="k in classes" :key="k.cohort_code" class="sidebar-card">
            <div class="card-top">
              <div class="card-title">{{ k.cohort_name }}</div>
            </div>
            <div class="card-meta">所属课程：{{ k.series_code }}</div>
            <div class="card-meta">开课日期：{{ k.start_date }} ~ {{ k.end_date || '—' }}</div>
            <div class="card-meta">售价：{{ formatAmount(k.sale_price) }}</div>
            <div class="card-meta">班次编码：{{ k.cohort_code }}</div>
            <button
              type="button"
              class="primary-outline full-width"
              :disabled="isSending"
              @click="sendClass(k)"
            >
              发送班次对象
            </button>
          </article>
        </div>

        <div v-else class="sidebar-list">
          <div v-if="!orders.length && !isLoadingSidebar" class="sidebar-empty">
            暂无订单数据
          </div>

          <article v-for="order in orders" :key="order.order_no" class="sidebar-card">
            <div class="card-top">
              <div class="card-title">订单 {{ order.order_no }}</div>
              <div class="card-amount">{{ formatAmount(order.amount) }}</div>
            </div>
            <div class="card-meta">订单状态：{{ order.status_desc || order.order_status }}</div>
            <div class="card-meta">创建时间：{{ order.created_at }}</div>
            <button
              type="button"
              class="primary-outline full-width"
              :disabled="isSending"
              @click="sendOrder(order)"
            >
              发送订单对象
            </button>
          </article>
        </div>
      </aside>
    </div>

    <footer class="status-bar">
      <span>Vite 代理：<code>/api</code> → <code>http://127.0.0.1:8012</code></span>
      <span class="sep">·</span>
      <span>业务服务：<code>/edu</code> → <code>http://127.0.0.1:9001</code></span>
      <span class="sep">·</span>
      <span>请先启动 <code>edu-service-backend</code> 再试聊天与历史接口。</span>
    </footer>
  </div>
</template>

<style scoped>
:global(*) {
  box-sizing: border-box;
}

:global(body) {
  margin: 0;
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: linear-gradient(165deg, #f0f7ff 0%, #e8f4ef 45%, #f5f0ff 100%);
  color: #152032;
}

:global(button),
:global(input) {
  font: inherit;
}

#app {
  min-height: 100vh;
}

.app-shell {
  min-height: 100vh;
  padding: 20px 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 18px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(100, 116, 139, 0.2);
  box-shadow: 0 12px 40px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(10px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  font-size: 28px;
  line-height: 1;
}

.brand-title {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.brand-sub {
  margin-top: 2px;
  font-size: 13px;
  color: #5b6b82;
}

.top-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
}

.pill {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(14, 116, 144, 0.12);
  color: #0f766e;
  font-weight: 600;
}

.sender-pill {
  font-size: 13px;
  color: #475569;
}

.workspace {
  flex: 1;
  min-height: 0;
  width: min(1760px, 100%);
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 18px;
  align-items: stretch;
}

.chat-card,
.sidebar {
  min-height: calc(100vh - 200px);
  height: calc(100vh - 200px);
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(100, 116, 139, 0.18);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.07);
  backdrop-filter: blur(12px);
}

.chat-card {
  display: flex;
  flex-direction: column;
}

.chat-inner-header {
  padding: 20px 22px 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.22);
}

.chat-inner-header h1 {
  margin: 0;
  font-size: 22px;
  letter-spacing: -0.02em;
}

.muted {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 14px;
  line-height: 1.6;
}

.muted.small {
  margin: 6px 0 0;
  font-size: 13px;
}

.controls {
  padding: 14px 22px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field span {
  color: #475569;
  font-size: 13px;
  font-weight: 600;
}

.field-row {
  display: flex;
  gap: 10px;
}

.field input {
  flex: 1;
  min-width: 0;
}

.field input,
.composer input {
  min-height: 44px;
  padding: 10px 14px;
  border: 1px solid rgba(148, 163, 184, 0.45);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.92);
  color: #0f172a;
  font-size: 15px;
}

.messages {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  scrollbar-gutter: stable;
  padding: 18px 22px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.empty-state {
  margin: auto;
  max-width: 440px;
  color: #64748b;
  text-align: center;
  line-height: 1.75;
  font-size: 14px;
}

.message {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: min(82%, 760px);
}

.message.user {
  align-self: flex-end;
}

.message.bot {
  align-self: flex-start;
}

.message.divider {
  align-self: stretch;
  max-width: none;
}

.history-divider {
  display: flex;
  align-items: center;
  gap: 14px;
  color: #7a8aa3;
  font-size: 13px;
}

.history-divider::before,
.history-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(148, 163, 184, 0.36);
}

.history-divider span {
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(241, 245, 249, 0.95);
  border: 1px solid rgba(148, 163, 184, 0.25);
}

.meta {
  font-size: 12px;
  color: #94a3b8;
}

.bubble {
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.22);
}

.message.user .bubble {
  background: linear-gradient(135deg, #0d9488, #0891b2);
  border-color: transparent;
  color: #ecfeff;
  box-shadow: 0 10px 28px rgba(13, 148, 136, 0.22);
}

.message.bot .bubble {
  background: rgba(255, 255, 255, 0.96);
  color: #0f172a;
}

.bubble p {
  margin: 0;
  font-size: 15px;
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;
}

.object-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 220px;
}

.object-card-badge {
  width: fit-content;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(15, 23, 42, 0.06);
  color: #334155;
}

.message.user .object-card-badge {
  background: rgba(255, 255, 255, 0.2);
  color: #ecfeff;
}

.object-card-title {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.45;
}

.object-card-meta {
  font-size: 14px;
  opacity: 0.92;
}

.object-card-price {
  font-size: 15px;
  font-weight: 700;
}

.error-message {
  margin: 0;
  padding: 0 22px 10px;
  color: #c2410c;
  font-size: 14px;
}

.composer {
  flex-shrink: 0;
  display: flex;
  gap: 10px;
  padding: 14px 22px 18px;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(248, 250, 252, 0.85);
}

.composer button {
  min-width: 96px;
  padding: 10px 16px;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  font-weight: 700;
  background: linear-gradient(135deg, #6366f1, #7c3aed);
  color: #fff;
  box-shadow: 0 12px 28px rgba(99, 102, 241, 0.25);
}

.composer button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  box-shadow: none;
}

.secondary-button,
.tab-button,
.primary-outline {
  min-height: 40px;
  padding: 8px 14px;
  border-radius: 12px;
  border: 1px solid rgba(100, 116, 139, 0.35);
  background: rgba(255, 255, 255, 0.9);
  color: #0f172a;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
}

.secondary-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.sidebar {
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 18px 20px 10px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
}

.sidebar-header h2 {
  margin: 0;
  font-size: 18px;
}

.tabs {
  display: flex;
  gap: 8px;
  padding: 12px 16px 10px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
}

.tab-button {
  flex: 1;
  min-width: 0;
  font-size: 13px;
}

.tab-button.active {
  background: linear-gradient(135deg, #0f766e, #0891b2);
  border-color: transparent;
  color: #ecfeff;
}

.sidebar-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 14px 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sidebar-card {
  padding: 14px;
  border-radius: 14px;
  border: 1px solid rgba(148, 163, 184, 0.28);
  background: rgba(248, 250, 252, 0.85);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.card-top {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: flex-start;
}

.card-title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.45;
}

.card-amount {
  flex-shrink: 0;
  font-weight: 800;
  color: #0f172a;
}

.card-meta {
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
}

.line-clamp {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.primary-outline {
  width: 100%;
  background: rgba(255, 255, 255, 0.95);
  border-color: rgba(99, 102, 241, 0.45);
  color: #4f46e5;
}

.primary-outline:hover:not(:disabled) {
  background: rgba(238, 242, 255, 0.95);
}

.primary-outline:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.sidebar-empty {
  margin: auto;
  text-align: center;
  color: #94a3b8;
  font-size: 14px;
  padding: 24px 8px;
}

.sidebar-error {
  margin: 0;
  padding: 8px 16px 0;
  color: #c2410c;
  font-size: 13px;
}

.status-bar {
  font-size: 12px;
  color: #64748b;
  padding: 0 4px;
}

.status-bar code {
  font-size: 12px;
  background: rgba(15, 23, 42, 0.06);
  padding: 2px 6px;
  border-radius: 6px;
}

.sep {
  margin: 0 6px;
  color: #cbd5e1;
}

.full-width {
  width: 100%;
}

@media (max-width: 1180px) {
  .workspace {
    grid-template-columns: 1fr;
  }

  .chat-card,
  .sidebar {
    height: auto;
    min-height: 420px;
  }
}

@media (max-width: 720px) {
  .app-shell {
    padding: 12px;
  }

  .top-bar {
    flex-direction: column;
    align-items: flex-start;
  }

  .composer,
  .field-row {
    flex-direction: column;
  }
}
</style>
