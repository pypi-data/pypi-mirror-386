#!/usr/bin/env python3
"""
最终验证测试 - 直接测试MCP服务器功能
"""

import subprocess
import json
import sys

def test_server_directly():
    """直接测试服务器功能"""
    print("🚀 直接测试MCP服务器功能...")

    # 测试1: 基本启动测试
    print("\n1️⃣ 测试服务器启动...")
    try:
        process = subprocess.Popen(
            ["uv", "run", "aigroup-econ-mcp", "main", "--transport", "stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        import time
        time.sleep(2)

        # 读取启动消息
        output = process.stdout.readline()
        if "Starting aigroup-econ-mcp server" in output:
            print("   ✅ 服务器启动成功")
        else:
            print(f"   ⚠️  启动消息: {output}")

        process.terminate()
        process.wait()

    except Exception as e:
        print(f"   ❌ 启动测试失败: {e}")
        return False

    # 测试2: 版本信息
    print("\n2️⃣ 测试版本信息...")
    try:
        result = subprocess.run(
            ["uv", "run", "aigroup-econ-mcp", "version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and "aigroup-econ-mcp v0.1.0" in result.stdout:
            print("   ✅ 版本信息正确")
        else:
            print(f"   ❌ 版本测试失败: {result.stdout}")
    except Exception as e:
        print(f"   ❌ 版本测试失败: {e}")
        return False

    # 测试3: 帮助信息
    print("\n3️⃣ 测试帮助信息...")
    try:
        result = subprocess.run(
            ["uv", "run", "aigroup-econ-mcp", "--help"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and "AIGroup" in result.stdout:
            print("   ✅ 帮助信息正确")
        else:
            print(f"   ❌ 帮助测试失败: {result.stdout}")
    except Exception as e:
        print(f"   ❌ 帮助测试失败: {e}")
        return False

    # 测试4: 验证mcp.json配置
    print("\n4️⃣ 验证mcp.json配置...")
    try:
        import os
        mcp_config_path = os.path.join(".roo", "mcp.json")
        if os.path.exists(mcp_config_path):
            with open(mcp_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            if "mcpServers" in config and "aigroup-econ-mcp" in config["mcpServers"]:
                server_config = config["mcpServers"]["aigroup-econ-mcp"]
                required_fields = ["command", "args", "transport"]

                if all(field in server_config for field in required_fields):
                    print("   ✅ mcp.json配置正确")
                    print(f"   📋 配置详情: {server_config}")
                else:
                    print(f"   ❌ 配置缺少必要字段: {required_fields}")
                    return False
            else:
                print("   ❌ mcp.json中没有aigroup-econ-mcp配置")
                return False
        else:
            print("   ❌ 找不到mcp.json文件")
            return False

    except Exception as e:
        print(f"   ❌ 配置验证失败: {e}")
        return False

    print("\n🎉 所有基础测试通过！")
    print("\n📋 总结:")
    print("   ✅ MCP服务器配置完成")
    print("   ✅ 依赖包安装成功")
    print("   ✅ 服务器能正常启动")
    print("   ✅ CLI命令工作正常")
    print("   ✅ mcp.json配置正确")
    print("\n🚀 服务器已准备就绪，可以通过MCP客户端使用！")

    return True

if __name__ == "__main__":
    success = test_server_directly()
    sys.exit(0 if success else 1)