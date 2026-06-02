from pathlib import Path

p = Path('custom_components/awenta_ahr/fan.py')
text = p.read_text(encoding='utf-8')
text = text.replace('\r\n', '\n')
old = '''    async def async_turn_off(self, **kwargs):

        await self.api.send(
            self.mac,
            {
                "act": "send_gear_number",
                "gear_nr": 0,
            },
        )
'''
new = '''    async def async_turn_off(self, **kwargs):

        await self.api.send(
            self.mac,
            {
                "act": "send_power_off",
            },
        )

    async def async_turn_on(self, percentage=None, **kwargs):
        if percentage is None:
            if getattr(self, "_last_percentage", None):
                await self.async_set_percentage(self._last_percentage)
                return
            await self.api.send(
                self.mac,
                {
                    "act": "send_power_on",
                },
            )
            return

        await self.async_set_percentage(percentage)
'''
if old not in text:
    raise SystemExit('old block not found')
text = text.replace(old, new)
p.write_text(text.replace('\n', '\r\n'), encoding='utf-8')
print('patched')
