from __future__ import annotations
import argparse, asyncio
from appgestaoti_agent.config import Config
from appgestaoti_agent.logging_config import setup_logging
from appgestaoti_agent.services.agent_service import AgentService

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True, help="Caminho para config.toml")
    p.add_argument("--iterations", type=int, default=None, help="Apenas para dev/teste")
    p.add_argument("--log-level", default="INFO")
    return p.parse_args()

def main():
    args = parse_args()
    setup_logging(args.log_level)
    cfg = Config.from_file(args.config)
    svc = AgentService(cfg)
    asyncio.run(svc.start(iterations=args.iterations))

if __name__ == "__main__":
    main()
