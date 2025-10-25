"""
AIGroup 计量经济学 MCP 服务命令行入口
"""

import click
import uvicorn
from .server import create_mcp_server


@click.command()
@click.option('--port', default=8000, help='服务器端口')
@click.option('--host', default='127.0.0.1', help='服务器地址')
@click.option('--transport', default='streamable-http',
              type=click.Choice(['stdio', 'streamable-http', 'sse']),
              help='传输协议')
@click.option('--debug', is_flag=True, help='启用调试模式')
@click.option('--mount-path', default=None, help='挂载路径')
def main(port: int, host: str, transport: str, debug: bool, mount_path: str):
    """启动aigroup-econ-mcp服务器"""

    # 创建MCP服务器
    mcp_server = create_mcp_server()

    # 设置调试模式
    if debug:
        mcp_server.settings.debug = True
        click.echo(f"[DEBUG] 调试模式已启用")

    click.echo(f"[INFO] Starting aigroup-econ-mcp server")
    click.echo(f"[INFO] Professional econometrics MCP tool for AI data analysis")
    click.echo(f"[INFO] Transport protocol: {transport}")
    click.echo(f"[INFO] Service address: http://{host}:{port}")
    if mount_path:
        click.echo(f"[INFO] Mount path: {mount_path}")

    # 根据传输协议启动服务器
    if transport == 'stdio':
        # stdio模式直接运行
        mcp_server.run(transport='stdio')
    elif transport == 'streamable-http':
        # Streamable HTTP模式
        mcp_server.run(
            transport='streamable-http',
            host=host,
            port=port,
            mount_path=mount_path or '/mcp'
        )
    elif transport == 'sse':
        # SSE模式
        mcp_server.run(
            transport='sse',
            host=host,
            port=port,
            mount_path=mount_path or '/sse'
        )


@click.command()
def version():
    """Show version information"""
    click.echo("aigroup-econ-mcp v0.1.0")
    click.echo("Professional econometrics MCP tool")
    click.echo("Author: AIGroup")


@click.group()
def cli():
    """AIGroup 计量经济学 MCP 工具"""
    pass


# 添加子命令
cli.add_command(main)
cli.add_command(version)


if __name__ == "__main__":
    cli()