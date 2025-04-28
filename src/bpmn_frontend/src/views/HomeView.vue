<template>
  <!-- 主容器 -->
  <div style="display: flex; flex-direction: row; height: 100vh">
    <div class="chat-container">
      <!-- 反馈请求事件 -->
      <!-- 用户消息事件 -->
      <!-- AI回复事件 -->
      <!-- BPMN XML接收事件 -->
      <!-- BPMN JSON接收事件 -->
      <!-- 下载事件 -->
      <!-- 下载按钮状态 -->
      <!-- 当前流程数据 -->
      <ChatInterface
        @feedback-requested="showFeedbackDialog = true"   
        @user-message="handleUserMessage"                 
        @assistant-message="handleAssistantMessage"
        @bpmn-xml-received="handleBpmnXml"
        @bpmn-json-received="setBpmnJson"
        @download="downloadBpmnFile"
        :isDownloadReady="!!bpmnXml"
        :process="process"
      />
    </div>
    <div
      id="canvas"
      class="canvas-container"
      @dragover.prevent
      @drop="handleDrop"
    ></div>
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>

    <!-- 新增反馈对话框 -->
    <v-dialog v-model="showFeedbackDialog" max-width="1200" persistent>
      <v-card>
        <v-card-title class="headline">提交反馈</v-card-title>
        <v-card-text>
          <div style="display: flex; gap: 20px; height: 500px;">
            <!-- 左侧聊天记录 -->
            <div style="flex: 1; overflow-y: auto;">
              <h3>聊天记录</h3>
              <div
                  v-for="(msg, index) in chatHistory"
                  :key="index"
                  class="message-item"
                  :class="{ 'user-message': msg.role === 'user', 'ai-message': msg.role === 'assistant' }"
              >
                {{ msg.content }}
              </div>
            </div>

            <!-- 右侧BPMN XML -->
            <div style="flex: 1; overflow-y: auto;">
              <h3>BPMN XML</h3>
              <pre class="xml-preview">{{ formattedBpmnXml }}</pre>
            </div>
          </div>

          <!-- 备注输入 -->
          <v-textarea
              v-model="feedbackComment"
              label="备注"
              outlined
              rows="3"
              class="mt-4"
          ></v-textarea>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="submitFeedback">确认</v-btn>
          <v-btn color="grey" @click="cancelFeedback">取消</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import BpmnModeler from 'bpmn-js/lib/Modeler';
import ChatInterface from '../components/ChatInterface.vue';
// import initialDiagram from "../assets/initialDiagram.js";
import 'bpmn-js/dist/assets/diagram-js.css';
import 'bpmn-js/dist/assets/bpmn-js.css';
import 'bpmn-js/dist/assets/bpmn-font/css/bpmn-embedded.css';

export default {
  name: 'App',
  components: {
    ChatInterface,
  },
  data() {
    return {
      bpmnXml: '',
      process: null, // Process in JSON format
      bpmnViewer: null,
      snackbar: {
        show: false,
        text: '',
        color: 'success',
      },
      showFeedbackDialog: false,
      feedbackComment: '',
      chatHistory: [],
    };
  },
  mounted() {
    this.bpmnViewer = new BpmnModeler({
      container: '#canvas',
    });

    // this.bpmnViewer
    //   .importXML(initialDiagram)
    //   .then((result) => {
    //     const { warnings } = result;
    //     console.log("BPMN diagram imported successfully", warnings);
    //     this.bpmnViewer.get("canvas").zoom("fit-viewport");
    //   })
    //   .catch((err) => {
    //     console.error("Failed to import BPMN diagram:", err);
    //   });
  },
  beforeUnmount() {
    if (this.bpmnViewer) {
      this.bpmnViewer.destroy();
    }
  },
  computed: {
    formattedBpmnXml() {
      if (!this.bpmnXml) return 'No BPMN content';
      return this.formatXml(this.bpmnXml);
    }
  },
  methods: {
    showSnackbar(text, color = 'success') {
      this.snackbar.text = text;
      this.snackbar.color = color;
      this.snackbar.show = true;
    },
    async handleDrop(event) {
      event.preventDefault(); // Prevent the browser from default file handling
      if (event.dataTransfer.items) {
        for (let i = 0; i < event.dataTransfer.items.length; i++) {
          if (event.dataTransfer.items[i].kind === 'file') {
            const file = event.dataTransfer.items[i].getAsFile();

            if (file.name.endsWith('.bpmn')) {
              const reader = new FileReader();
              reader.onload = async (e) => {
                const xmlContent = e.target.result;
                try {
                  await this.bpmnViewer.importXML(xmlContent);
                  this.bpmnViewer.get('canvas').zoom('fit-viewport');
                  console.log('BPMN diagram loaded successfully');
                  this.bpmnXml = xmlContent;
                  await this.createBpmnJson();
                } catch (err) {
                  console.error('Failed to import BPMN diagram:', err);
                }
              };
              reader.readAsText(file);
            }
          }
        }
      }
    },
    async createBpmnJson() {
      try {
        const response = await fetch('http://localhost:8000/bpmn_to_json', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ bpmn_xml: this.bpmnXml }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }

        this.process = await response.json();
        console.log('BPMN JSON created successfully:', this.process);
        this.showSnackbar('BPMN successfully uploaded', 'success');
      } catch (error) {
        console.error('Error creating BPMN JSON:', error);
        this.showSnackbar(
          'There was a problem while loading the BPMN file',
          'error'
        );
      }
    },
    async handleBpmnXml(bpmnXmlValue) {
      if (bpmnXmlValue === '') {
        if (this.bpmnViewer) {
          this.bpmnViewer.destroy();
        }

        this.bpmnViewer = new BpmnModeler({
          container: '#canvas',
        });
        return;
      }

      try {
        // Auto-layout of the BPMN diagram
        const layoutedXml = await this.processDiagram(bpmnXmlValue);
        if (!layoutedXml) {
          throw new Error('Failed to layout the BPMN diagram');
        }
        this.bpmnXml = layoutedXml;
        if (this.bpmnViewer) {
          this.bpmnViewer
            .importXML(layoutedXml)
            .then((result) => {
              const { warnings } = result;
              console.log('BPMN diagram imported successfully', warnings);
              this.bpmnViewer.get('canvas').zoom('fit-viewport');
            })
            .catch((err) => {
              console.error('Failed to import BPMN diagram:', err);
            });
        }
      } catch (error) {
        console.error('Error handling BPMN XML:', error);
      }
    },
    async processDiagram(bpmnDiagram) {
      try {
        const response = await fetch('http://localhost:3001/process-bpmn', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ bpmnXml: bpmnDiagram }),
        });

        if (!response.ok) {
          throw new Error('Network response was not ok');
        }

        const { layoutedXml } = await response.json();

        console.log(layoutedXml);

        return layoutedXml;
      } catch (error) {
        console.error('Failed to process the diagram:', error);
      }
    },
    async downloadBpmnFile() {
      const { xml } = await this.bpmnViewer.saveXML();
      const blob = new Blob([xml], { type: 'text/xml' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'diagram.bpmn';
      a.click();
    },
    setBpmnJson(value) {
      this.process = value;
    },
    formatXml(xml) {
      const PADDING = ' '.repeat(2);
      const reg = /(>)(<)(\/*)/g;
      let pad = 0;

      xml = xml.replace(reg, '$1\r\n$2$3');

      return xml.split('\r\n').map(node => {
        let indent = 0;
        if (node.match(/.+<\/\w[^>]*>$/)) {
          indent = 0;
        } else if (node.match(/^<\/\w/)) {
          if (pad !== 0) pad -= 1;
        } else if (node.match(/^<\w[^>]*[^\/]>.*$/)) {
          indent = 1;
        } else {
          indent = 0;
        }

        pad += indent;
        return PADDING.repeat(pad - indent) + node;
      }).join('\r\n');
    },

    submitFeedback() {
      const payload = {
        chatHistory: this.chatHistory,
        bpmnXml: this.bpmnXml,
        comment: this.feedbackComment
      };
      console.log('Feedback payload:', payload);

      this.showSnackbar('反馈已提交成功', 'success');
      this.cancelFeedback();
    },

    cancelFeedback() {
      this.showFeedbackDialog = false;
      this.feedbackComment = '';
    },

    // 新增消息处理方法
    handleUserMessage(message) {
      this.chatHistory.push({
        role: 'user',
        content: message,
        timestamp: new Date().toISOString()
      });
    },

    handleAssistantMessage(content) {
      const lastMessage = this.chatHistory[this.chatHistory.length - 1];

      if (lastMessage && lastMessage.role === 'assistant') {
        lastMessage.content += content;
      } else {
        this.chatHistory.push({
          role: 'assistant',
          content: content,
          timestamp: new Date().toISOString()
        });
      }
    }
  }
};
</script>

<style>
#canvas {
  margin: 10px;
}

.chat-container {
  flex: 3;
}

.canvas-container {
  flex: 4;
  border: 2px solid gray;
}

@media (min-width: 1800px) {
  .chat-container {
    flex: 2;
  }
  .canvas-container {
    flex: 5;
  }
}
/* 新增样式 */
.message-item {
  margin: 8px 0;
  padding: 8px 12px;
  border-radius: 8px;
  word-break: break-word;
}

.user-message {
  background: #e3f2fd;
  margin-left: 20%;
}

.ai-message {
  background: #f5f5f5;
  margin-right: 20%;
}

.xml-preview {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 4px;
  max-height: 400px;
  overflow: auto;
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 0.9em;
}
</style>
