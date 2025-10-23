import click

from mcp_generate_mind import start_server


# 通过clik设置命令行启动参数
@click.command()
@click.option("--port", default=3000, help="Port to listen on for HTTP")
@click.option("--host", default="127.0.0.1", help="Host for HTTP")
@click.option(
    "--log-level",
    default="INFO",
    help="日志级别(DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--mcp-type",
    default="sse",
    help="mcp传输的模式：sse/streamable-http",
)
def main(port, host, log_level, mcp_type):
    start_server.main(mcp_type)


if __name__ == "__main__":
    main()
