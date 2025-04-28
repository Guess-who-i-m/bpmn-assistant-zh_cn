# 

## 添加模型的说明

1. 在/bpmn_assistant/core/enums/models.py中添加供应商和模型
2. 在/bpmn_assistant/core/enums/__init__.py中添加供应商和模型
3. 在/bpmn_assistant/core/enums/providers.py中添加供应商信息
4. 在/bpmn_assistant/core/provider_impl下创建一个供应商的py，实现供应商类，具体实现参考阿里的ali_provider
5. 在/bpmn_assistant/core/provider_impl/__init__.py添加你所新增的供应商信息
6. 之后在/bpmn_assistant/core/provider_factory中添加相关判断逻辑
7. 在/bpmn_assistant/utils/utils.py中添加一个模型判断函数，并引用模型