from eth_vertigo.core.campaign import BaseCampaign
from typing import List
from eth_vertigo.mutator.mutator import Mutator
from pathlib import Path
from eth_vertigo.core.network import NetworkPool
from json import loads

class HardhatCampaign(BaseCampaign):
    def __init__(
            self,
            hardhat_command: str,
            project_directory: Path,
            mutators: List[Mutator],
            network_pool: NetworkPool,
            filters=None,
            suggesters=None
    ):
        from eth_vertigo.interfaces.hardhat.tester import HardhatTester
        from eth_vertigo.interfaces.hardhat.compile import HardhatCompiler
        from eth_vertigo.interfaces.hardhat.mutator import HardhatSourceFile

        compiler = HardhatCompiler(hardhat_command)
        tester = HardhatTester(hardhat_command, str(project_directory), compiler)
        source_file_builder = lambda path: HardhatSourceFile(path)

        super().__init__(
            project_directory=project_directory,
            mutators=mutators,
            network_pool=network_pool,

            compiler=compiler,
            tester=tester,
            source_file_builder=source_file_builder,

            filters=filters,
            suggesters=suggesters
        )

    def _get_sources(self):
        """ Implements basic mutator file discovery """

        contracts_dir = self.project_directory / "artifacts" / "contracts"
        if not contracts_dir.exists():
            self.compiler.run_compilation(str(self.project_directory))

        for contract_dir in contracts_dir.iterdir():
            for contract in [c for c in contract_dir.iterdir() if "dbg.json" not in c.name]:
                dbg_json = contract_dir / contract.name.replace('.json', '.dbg.json')

                contract = loads(contract.read_text("utf-8"))
                dbg = loads(dbg_json.read_text("utf-8"))

                source_name = contract["sourceName"]
                build_info_file = contract_dir / dbg["buildInfo"]
                build_info = loads(dbg_json.read_text("utf-8"))

                ast = build_info["output"]["sources"]["sourceName"]["ast"]
                full_path = ast["fullPath"]

                yield self.source_file_builder(ast, full_path)