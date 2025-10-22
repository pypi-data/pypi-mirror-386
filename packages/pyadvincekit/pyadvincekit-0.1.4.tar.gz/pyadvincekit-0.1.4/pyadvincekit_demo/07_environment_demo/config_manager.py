"""
阶段一：配置管理示例

演示 PyAdvanceKit 的配置管理功能：
- 多环境配置
- 环境变量覆盖
- 配置验证
- 自定义配置
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pyadvincekit.core.config import Settings, Environment, LogLevel


def example_basic_config():
    """基础配置示例"""
    print("=== 基础配置示例 ===")

    # 创建默认配置
    settings = Settings()

    print(f"应用名称: {settings.app_name}")
    print(f"运行环境: {settings.environment}")
    print(f"调试模式: {settings.debug}")
    print(f"服务器地址: {settings.host}:{settings.port}")
    print(f"数据库URL: {settings.database_url}")
    print(f"日志级别: {settings.log_level}")
    print()


def example_environment_config():
    """环境配置示例"""
    print("=== 环境配置示例 ===")

    # 开发环境
    dev_settings = Settings(environment="development")
    print(f"开发环境 - Debug: {dev_settings.debug}")
    print(f"开发环境 - 文档URL: {dev_settings.docs_url}")

    # 测试环境
    test_settings = Settings(environment="testing")
    print(f"测试环境 - Debug: {test_settings.debug}")
    print(f"测试环境 - 文档URL: {test_settings.docs_url}")

    # 生产环境
    prod_settings = Settings(environment="production")
    print(f"生产环境 - Debug: {prod_settings.debug}")
    print(f"生产环境 - 文档URL: {prod_settings.docs_url}")
    print()


def example_custom_config():
    """自定义配置示例"""
    print("=== 自定义配置示例 ===")

    # 自定义配置参数
    custom_settings = Settings(
        app_name="我的应用",
        environment="development",
        port=8080,
        database_url="postgresql://user:pass@localhost/mydb",
        database_pool_size=20,
        log_level="DEBUG",
        log_file_enabled=True,
        log_file_path="logs/my_app.log"
    )

    print(f"应用名称: {custom_settings.app_name}")
    print(f"服务器端口: {custom_settings.port}")
    print(f"数据库URL: {custom_settings.database_url}")
    print(f"连接池大小: {custom_settings.database_pool_size}")
    print(f"SQL日志: {custom_settings.database_echo_sql}")
    print(f"日志级别: {custom_settings.log_level}")
    print(f"日志文件: {custom_settings.log_file_path}")
    print()


def example_environment_variables():
    """环境变量配置示例"""
    print("=== 环境变量配置示例 ===")

    # 设置环境变量
    os.environ["PYADVINCEKIT_APP_NAME"] = "环境变量应用"
    os.environ["PYADVINCEKIT_PORT"] = "9000"
    os.environ["PYADVINCEKIT_DEBUG"] = "false"
    os.environ["PYADVINCEKIT_DATABASE_URL"] = "sqlite:///env_test.db"

    # 创建配置（会自动读取环境变量）
    env_settings = Settings()

    print(f"应用名称: {env_settings.app_name}")
    print(f"服务器端口: {env_settings.port}")
    print(f"调试模式: {env_settings.debug}")
    print(f"数据库URL: {env_settings.database_url}")

    # 清理环境变量
    for key in ["PYADVINCEKIT_APP_NAME", "PYADVINCEKIT_PORT",
                "PYADVINCEKIT_DEBUG", "PYADVINCEKIT_DATABASE_URL"]:
        os.environ.pop(key, None)
    print()


def example_database_url_conversion():
    """数据库URL转换示例"""
    print("=== 数据库URL转换示例 ===")

    settings = Settings()

    # 设置不同类型的数据库URL
    database_urls = [
        "postgresql://user:pass@localhost/db",
        "mysql://user:pass@localhost/db",
        "sqlite:///./test.db"
    ]

    for url in database_urls:
        settings.database_url = url

        sync_url = settings.get_database_url(async_driver=False)
        async_url = settings.get_database_url(async_driver=True)

        print(f"原始URL: {url}")
        print(f"同步URL: {sync_url}")
        print(f"异步URL: {async_url}")
        print("-" * 50)
    print()


if __name__ == "__main__":
    print("🚀 PyAdvanceKit 配置管理示例")
    print("=" * 50)

    # 运行所有示例
    example_basic_config()
    example_environment_config()
    example_custom_config()
    example_environment_variables()
    example_database_url_conversion()

    print("✅ 配置管理示例完成！")
    print("提示:")
    print("1. 在生产环境中，请使用环境变量或 .env 文件设置敏感配置")
    print("2. 不同环境可以使用不同的配置文件")
    print("3. 所有配置都有类型验证，确保配置的正确性")
