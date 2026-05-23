@echo off
REM RabbitMQ 队列清理脚本
REM 运行此脚本删除所有 rag_* 队列，然后重启服务

echo 正在连接 RabbitMQ...

docker exec dev-rabbitmq rabbitmqctl delete_queue rag_parse_queue 2>nul
echo 删除 rag_parse_queue

docker exec dev-rabbitmq rabbitmqctl delete_queue rag_clean_queue 2>nul
echo 删除 rag_clean_queue

docker exec dev-rabbitmq rabbitmqctl delete_queue rag_chunk_queue 2>nul
echo 删除 rag_chunk_queue

docker exec dev-rabbitmq rabbitmqctl delete_queue rag_embedding_queue 2>nul
echo 删除 rag_embedding_queue

docker exec dev-rabbitmq rabbitmqctl delete_queue rag_index_queue 2>nul
echo 删除 rag_index_queue

docker exec dev-rabbitmq rabbitmqctl delete_queue rag_dlx_queue 2>nul
echo 删除 rag_dlx_queue

echo.
echo 所有队列已删除！
echo.
echo 请重启后端服务和 Worker。
echo.
pause
