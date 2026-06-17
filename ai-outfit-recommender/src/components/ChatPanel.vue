<template>
  <div class="chat-panel">
    <div class="chat-header">
      <span class="chat-title">AI 衣橱助手</span>
      <el-button link size="small" @click="clearChat" title="清空对话">
        <el-icon><Delete /></el-icon>
      </el-button>
    </div>

    <div class="chat-messages" ref="msgContainer">
      <!-- 欢迎消息 -->
      <div v-if="messages.length === 0" class="welcome-msg">
        <div class="welcome-icon">👗</div>
        <p>你好！我是你的AI衣橱助手</p>
        <p class="welcome-hint">试试问我：</p>
        <div class="quick-prompts">
          <span class="prompt-chip" @click="quickAsk('我有什么外套？')">我有什么外套？</span>
          <span class="prompt-chip" @click="quickAsk('今天穿什么好？')">今天穿什么好？</span>
          <span class="prompt-chip" @click="quickAsk('推荐一套上班穿搭')">推荐上班穿搭</span>
          <span class="prompt-chip" @click="quickAsk('北京今天天气怎么样？')">查天气</span>
        </div>
      </div>

      <div
        v-for="msg in messages"
        :key="msg.id"
        :class="['message', msg.role]"
      >
        <div class="msg-avatar">
          <span v-if="msg.role === 'user'">👤</span>
          <span v-else>🤖</span>
        </div>
        <div class="msg-body">
          <div class="msg-content" v-html="renderContent(msg.content)"></div>
          <!-- Agent 工具调用轨迹 -->
          <div v-if="msg.trace && msg.trace.length > 0" class="trace-info">
            <div class="trace-label">
              🔧 调用了 {{ msg.trace.length }} 个工具
            </div>
            <details class="trace-details">
              <summary>查看详情</summary>
              <div v-for="(step, idx) in msg.trace" :key="idx" class="trace-step">
                <span class="trace-num">{{ step.iteration || idx + 1 }}.</span>
                <span class="trace-tool">{{ step.tool }}</span>
                <span class="trace-args">{{ formatArgs(step.args) }}</span>
              </div>
            </details>
          </div>
          <!-- 加载中状态 -->
          <div v-if="msg.loading" class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <div class="chat-input-area">
      <textarea
        ref="inputRef"
        v-model="inputText"
        @keydown.enter.exact.prevent="send"
        placeholder="问我穿搭问题..."
        rows="1"
        :disabled="loading"
        class="chat-textarea"
      />
      <button
        @click="send"
        :disabled="loading || !inputText.trim()"
        class="send-btn"
      >
        <span v-if="loading">⏳</span>
        <span v-else>➤</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue';
import { Delete } from '@element-plus/icons-vue';

const msgContainer = ref(null);
const inputRef = ref(null);
const inputText = ref('');
const loading = ref(false);
const messages = ref([]);
const sessionId = ref(null);
let msgIdCounter = 0;

const scrollToBottom = () => {
  nextTick(() => {
    if (msgContainer.value) {
      msgContainer.value.scrollTop = msgContainer.value.scrollHeight;
    }
  });
};

const renderContent = (content) => {
  if (!content) return '';
  // 简单的 markdown-like 渲染
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
};

const formatArgs = (args) => {
  if (!args) return '';
  if (typeof args === 'string') return args;
  return JSON.stringify(args);
};

const quickAsk = (text) => {
  inputText.value = text;
  send();
};

const send = async () => {
  const text = inputText.value.trim();
  if (!text || loading.value) return;

  inputText.value = '';
  loading.value = true;

  // 添加用户消息
  const userMsg = {
    id: ++msgIdCounter,
    role: 'user',
    content: text,
  };
  messages.value.push(userMsg);
  scrollToBottom();

  // 添加AI加载消息
  const aiMsg = {
    id: ++msgIdCounter,
    role: 'assistant',
    content: '',
    loading: true,
    trace: [],
  };
  messages.value.push(aiMsg);
  scrollToBottom();

  try {
    const token = localStorage.getItem('auth_token');
    const resp = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        question: text,
        session_id: sessionId.value,
      }),
    });

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const data = line.slice(6).trim();

        if (data === '[DONE]') {
          aiMsg.loading = false;
          continue;
        }

        try {
          const event = JSON.parse(data);

          switch (event.type) {
            case 'session_id':
              sessionId.value = event.session_id;
              break;
            case 'thinking':
              aiMsg.content = event.message;
              scrollToBottom();
              break;
            case 'tool_call':
              aiMsg.trace.push({
                tool: event.tool,
                args: event.args,
                iteration: aiMsg.trace.length + 1,
              });
              aiMsg.content = `正在调用 ${event.tool}...`;
              scrollToBottom();
              break;
            case 'tool_result':
              // 工具结果已记录
              break;
            case 'answer':
              aiMsg.content = event.answer;
              aiMsg.trace = event.agent_trace || aiMsg.trace;
              aiMsg.loading = false;
              scrollToBottom();
              break;
          }
        } catch (e) {
          // 解析错误，跳过
        }
      }
    }

    aiMsg.loading = false;
    if (!aiMsg.content) {
      aiMsg.content = '抱歉，未能获取回复。请检查网络连接后重试。';
    }
  } catch (error) {
    aiMsg.loading = false;
    aiMsg.content = `网络错误: ${error.message}`;
  }

  loading.value = false;
  scrollToBottom();
  nextTick(() => inputRef.value?.focus());
};

const clearChat = () => {
  messages.value = [];
  sessionId.value = null;
};

onMounted(() => {
  inputRef.value?.focus();
});
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0 12px;
  border-bottom: 1px solid rgba(0,0,0,0.06);
  margin-bottom: 12px;
}

.chat-title {
  font-size: 14px;
  font-weight: 600;
  color: #1d1d1f;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
  scroll-behavior: smooth;
}

.chat-messages::-webkit-scrollbar {
  width: 4px;
}
.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.1);
  border-radius: 4px;
}

/* 欢迎消息 */
.welcome-msg {
  text-align: center;
  padding: 20px 8px;
  color: #86868b;
}
.welcome-icon {
  font-size: 36px;
  margin-bottom: 8px;
}
.welcome-msg p {
  margin: 4px 0;
  font-size: 13px;
}
.welcome-hint {
  color: #aaa;
  font-size: 12px !important;
  margin-top: 12px !important;
}

.quick-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
  margin-top: 10px;
}
.prompt-chip {
  display: inline-block;
  padding: 6px 12px;
  background: rgba(99, 102, 241, 0.08);
  color: #6366f1;
  border-radius: 16px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.prompt-chip:hover {
  background: rgba(99, 102, 241, 0.15);
}

/* 消息 */
.message {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  align-items: flex-start;
}

.message.user {
  flex-direction: row-reverse;
}

.msg-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
  background: rgba(0,0,0,0.04);
}

.msg-body {
  max-width: 85%;
}

.msg-content {
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
  word-break: break-word;
}

.message.user .msg-content {
  background: #6366f1;
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .msg-content {
  background: rgba(0,0,0,0.04);
  color: #1d1d1f;
  border-bottom-left-radius: 4px;
}

/* 工具调用轨迹 */
.trace-info {
  margin-top: 4px;
  font-size: 11px;
}

.trace-label {
  color: #86868b;
  cursor: pointer;
}

.trace-details {
  margin-top: 4px;
  padding: 6px 8px;
  background: rgba(0,0,0,0.02);
  border-radius: 8px;
}

.trace-details summary {
  font-size: 11px;
  color: #86868b;
  cursor: pointer;
}

.trace-step {
  padding: 2px 0;
  font-size: 11px;
  color: #666;
}

.trace-num {
  font-weight: 600;
  margin-right: 4px;
}

.trace-tool {
  color: #6366f1;
  font-family: monospace;
}

.trace-args {
  color: #999;
  font-size: 10px;
}

/* 打字动画 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}
.typing-indicator span {
  width: 6px;
  height: 6px;
  background: #86868b;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-4px); opacity: 1; }
}

/* 输入区域 */
.chat-input-area {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid rgba(0,0,0,0.06);
}

.chat-textarea {
  flex: 1;
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 12px;
  padding: 8px 12px;
  font-size: 13px;
  font-family: inherit;
  resize: none;
  outline: none;
  background: rgba(255,255,255,0.6);
  transition: border-color 0.2s;
  max-height: 80px;
}
.chat-textarea:focus {
  border-color: #6366f1;
}

.send-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: #6366f1;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
  transition: all 0.2s;
}
.send-btn:disabled {
  background: #ddd;
  cursor: not-allowed;
}
.send-btn:not(:disabled):hover {
  background: #4f46e5;
  transform: scale(1.05);
}
</style>
