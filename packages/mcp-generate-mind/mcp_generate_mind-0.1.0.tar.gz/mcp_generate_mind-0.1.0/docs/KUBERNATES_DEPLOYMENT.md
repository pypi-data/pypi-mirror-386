# Kubernetes 部署指南：Mind Generate 服务

本指南详细介绍如何在Kubernetes集群中部署和管理Mind Generate服务。

## 前提条件

在开始部署前，请确保您已经满足以下要求：

-   已安装并配置好Kubernetes集群（版本1.19+）
-   已安装`kubectl`命令行工具并配置连接到您的集群
-   已安装Docker并能够构建镜像
-   （可选）已配置ingress控制器（如需要外部访问）

## 目录结构
kubernetes/
├── deployment.yaml # Deployment配置（管理Pod和副本）
├── service.yaml # Service、Ingress和HPA配置
├── config.yaml # ConfigMap和Secret配置
└── KUBERNETES_DEPLOYMENT_GUIDE.md # 部署指南（本文档）

text

## 部署步骤

### 1. 构建Docker镜像

在部署到Kubernetes之前，需要先构建Docker镜像：

```bash
cd /path/to/mind-generate
docker build -t mind-generate:latest .

# 如果需要推送到镜像仓库
# docker tag mind-generate:latest your-registry/mind-generate:latest
# docker push your-registry/mind-generate:latest
```
### 2. 准备配置文件
根据您的环境修改配置文件：

在deployment.yaml中，根据需要调整副本数量和资源限制

在service.yaml中，修改Ingress配置中的域名

在config.yaml中，更新ConfigMap中的配置参数

在config.yaml中，更新Secret中的敏感信息

### 3. 应用配置文件
按照以下顺序应用配置文件：

```bash
# 创建命名空间（可选）
kubectl create namespace mind-mcp

# 应用配置文件
kubectl apply -f kubernetes/config.yaml -n mind-generate
kubectl apply -f kubernetes/deployment.yaml -n mind-generate
kubectl apply -f kubernetes/service.yaml -n mind-generate
配置说明
Deployment 配置 (deployment.yaml)
```
#### 主要配置项说明：

replicas: Pod副本数量，默认为3

resources: 资源请求和限制，确保服务稳定运行

livenessProbe/readinessProbe/startupProbe: 健康检查配置，确保只有健康的Pod才能处理请求

env: 环境变量配置，与Docker Compose保持一致

Service 配置 (service.yaml)
#### 主要配置项说明：

Service: 提供稳定的访问端点和内部负载均衡

Ingress: 配置外部访问（需要调整域名）

HorizontalPodAutoscaler: 根据CPU和内存使用情况自动扩缩容

配置和密钥 (config.yaml)
ConfigMap: 存储非敏感配置信息

Secret: 存储敏感信息，如API密钥和数据库连接字符串

#### 常用操作
1 、查看部署状态
```bash
kubectl get all -n mind-generate
kubectl describe deployment mind-generate-deployment -n mind-generate
kubectl logs -f deployment/mind-generate-deployment -n mind-generate
```
2、扩缩容
手动扩缩容：

```bash
kubectl scale deployment mind-generate-deployment --replicas=5 -n mind-generate
更新部署
修改配置文件后，应用更新：

bash
kubectl apply -f kubernetes/deployment.yaml -n mind-generate
```
3、滚动更新
```bash
# 修改镜像版本
kubectl set image deployment/mind-generate-deployment mind-generate=new-image:tag -n mind-generate

# 查看滚动更新状态
kubectl rollout status deployment/mind-generate-deployment -n mind-generate

# 回滚到之前的版本
kubectl rollout undo deployment/mind-generate-deployment -n mind-generate
```

4、获取Pod日志
```bash
# 获取特定Pod的日志
kubectl logs <pod-name> -n mind-generate

# 跟踪日志输出
kubectl logs -f <pod-name> -n mind-generate

# 获取所有Pod的日志
kubectl logs -l app=mind-generate -n mind-generate
```
5、环境变量参考
以下是主要的环境变量配置：

环境变量	描述	默认值
MCP_HOST	服务监听地址	0.0.0.0
MCP_PORT	服务监听端口	8000
MCP_DEBUG	是否启用调试模式	false
MCP_WORKERS	工作进程数量	4
MCP_LOG_LEVEL	日志级别	INFO
MCP_RESPONSE_TIMEOUT	响应超时时间（秒）	30

### 健康检查
服务提供了/health端点用于健康检查，Kubernetes会定期调用该端点来监控服务状态。

### 常见问题解决
Pod无法启动

检查Pod事件：kubectl describe pod <pod-name> -n mind-generate

检查Pod日志：kubectl logs <pod-name> -n mind-generate

验证镜像是否存在：docker pull mind-generate:latest

### 服务无法访问

检查Service状态：kubectl get svc -n mind-generate

检查Ingress配置：kubectl describe ingress mind-generate-ingress -n mind-generate

验证网络策略是否允许流量

自动扩缩容不工作

检查HPA状态：kubectl describe hpa mind-generate-hpa -n mind-generate

验证指标是否正确收集：kubectl top pods -n mind-generate

### 生产环境部署建议

使用命名空间：为不同环境（开发、测试、生产）创建单独的命名空间

持久化日志：配置日志持久化存储或集成日志收集系统

监控和告警：设置监控指标和告警规则

资源限制：根据实际负载调整资源请求和限制

### 安全措施：

使用Secret存储敏感信息

配置网络策略限制访问

定期更新镜像和依赖

备份策略：制定配置和数据备份策略
