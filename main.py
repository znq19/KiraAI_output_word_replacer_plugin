import re
from core.plugin import BasePlugin, logger, on, Priority
from core.chat.message_utils import KiraMessageBatchEvent
from core.chat.message_elements import Text


class OutputReplacerPlugin(BasePlugin):
    def __init__(self, ctx, cfg: dict):
        super().__init__(ctx, cfg)
        raw_rules = cfg.get("replacements", [])
        self.replacements = self._parse_rules(raw_rules)
        # 编译正则，提高性能
        self.patterns = {}
        for old, new in self.replacements.items():
            self.patterns[old] = (re.compile(re.escape(old)), new)

    def _parse_rules(self, rules: list) -> dict:
        mapping = {}
        if not rules:
            return mapping
        for item in rules:
            if not isinstance(item, str):
                continue
            item = item.strip()
            if not item or item.startswith('#'):
                continue
            if '/' in item:
                parts = item.split('/', 1)
                old = parts[0].strip()
                new = parts[1].strip()
                if old and new:
                    mapping[old] = new
            else:
                logger.warning(f"跳过无效规则: {item}")
        return mapping

    def _replace_text(self, text: str) -> str:
        if not text:
            return text
        for old, (pattern, new) in self.patterns.items():
            text = pattern.sub(new, text)
        return text

    async def initialize(self):
        logger.info(f"OutputReplacerPlugin initialized with {len(self.replacements)} replacement rules")

    async def terminate(self):
        pass

    @on.after_xml_parse(priority=Priority.HIGH)
    async def replace_xml_parsed(self, event: KiraMessageBatchEvent, message_chains: list):
        """在 AFTER_XML_PARSE 中修改消息链中的文本元素"""
        if not message_chains:
            return
        for chain in message_chains:
            for elem in chain.message_list:
                if isinstance(elem, Text):
                    original = elem.text
                    replaced = self._replace_text(original)
                    if replaced != original:
                        logger.info(f"替换文本: {original} -> {replaced}")
                        elem.text = replaced