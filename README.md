这个仓库继承自仓库 https://github.com/jtlicardo/bpmn-assistant ，感谢原作者对chat-bpmn工作做出的突出贡献，本项目的存在无意冒犯原作者的个人知识产权，仅用于记录本人在项目部署运行时做出的修改和轻微改进。在原项目中，用户可以直接使用大模型辅助创建、编辑、翻译BPMN图。在本项目中，主要对原项目做出了如下的更改：

- 增加了阿里云Qwen-max和Qwen-plus的访问接口，使得中国用户能够更加轻松的完成LLM的配置，体验LLM驱动的BPMN生成
- 增加了检索增强生成(RAG)的相关逻辑，生成BPMN前能够检索向量数据库中的知识，使得生成逻辑更贴近需求
- 将所有prompt逻辑翻译为中文

值得注意的是，本人对项目的部署并没有采用原作者给出的docker方法，而是直接通过运行vue和fast api项目完成部署。docker部署方法的准确性有待考量。

## 快速开始

1. 克隆这个仓库

```bash
git clone https://github.com/Guess-who-i-m/bpmn-assistant-zh_cn.git
```
```bash
cd bpmn-assistant
```

2. 设置环境变量
<details>
<summary>Linux, macOS</summary>

```
cd src/bpmn_assistant
```

```
cp .env.example .env
```

</details>

<details>
<summary>Windows</summary>

```bash
cd src/bpmn_assistant
```

```bash
copy .env.example .env
```

</details>

3. 打开刚刚复制的.env文件，把API-Key相关的内容放到里面。

4. 开始构建项目
<details>
  <summary>使用docker</summary>

  首先使用docker完成部署

  ```bash
  docker-compose up --build
  ```

  之后打开浏览器访问服务http://localhost:8080。
</details>
<details>
  <summary>原生构建</summary>

  采用这种方法，你首先需要拥有nodejs，vue和python(fastapi)的运行环境。

  首先构建后端环境，我们使用conda来管理环境。

  ```bash
  cd src/bpmn_assistant
  conda create -n bpmn_backend python=3.10
  conda activate bpmn_backend
  pip install -r requirements.txt
  ```
  
  完成环境配置后，运行fastapi启动命令即可。

  ```bash
  cd src/bpmn_assistant
  uvicorn app:app --host 0.0.0.0 --port 8000
  ```

  构建bpmn_layout_server
  ```bash
  cd src/bpmn_layout_server
  npm install
  node server.js
  ```

  最后构建前端

  ```bash
  cd src/bpmn_frontend
  npm install
  npm run dev
  ```
  之后打开vue渲染得到的前端页面即可正常使用服务。


</details>

## 支持的模型

### OpenAI

* GPT-4.1
* GPT-4.1 mini
* o4-mini

### Anthropic

* Claude 3.5 Haiku
* Claude 3.7 Sonnet

### Google

* Gemini 2.5 Flash
* Gemini 2.5 Pro

### Fireworks AI

* Llama 4 Maverick
* Qwen 2.5 72B
* Deepseek V3
* Deepseek R1

### 阿里云

* Qwen-max
* Qwen-plus
 

## 后续要做的事

2025-04-28 

当前版本尚不支持RAG功能的部署，等待后续有时间将RAG相关的逻辑添加到仓库中

后续将增加对docker环境下，自动部署的测试