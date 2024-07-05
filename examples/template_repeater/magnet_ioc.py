import asyncio
import json
from caproto.server import ioc_arg_parser, run, pvproperty, PVGroup
from caproto import ChannelType


class MagnetPV(PVGroup):
    bcon = pvproperty(
        value=0.0,
        name=":BCON",
        upper_ctrl_limit=0.006,
        lower_ctrl_limit=-0.006,
        upper_alarm_limit=0.004,
        lower_alarm_limit=-0.004,
        precision=4,
    )
    bdes = pvproperty(
        value=0.0,
        name=":BDES",
        upper_ctrl_limit=0.006,
        lower_ctrl_limit=-0.006,
        upper_alarm_limit=0.004,
        lower_alarm_limit=-0.004,
        precision=4,
    )
    bact = pvproperty(
        value=0.0,
        name=":BACT",
        read_only=True,
        upper_ctrl_limit=0.006,
        lower_ctrl_limit=-0.006,
        upper_alarm_limit=0.004,
        lower_alarm_limit=-0.004,
        precision=4,
    )
    ctrl_strings = (
        "Ready",
        "TRIM",
        "PERTURB",
        "BCON_TO_BDES",
        "SAVE_BDES",
        "LOAD_BDES",
        "UNDO_BDES",
        "DAC_ZERO",
        "CALB",
        "STDZ",
        "RESET",
        "TURN_ON",
        "TURN_OFF",
    )
    ctrl = pvproperty(value=0, name=":CTRL", dtype=ChannelType.ENUM, enum_strings=ctrl_strings)
    abort = pvproperty(value=0, name=":ABORT", dtype=ChannelType.ENUM, enum_strings=("Ready", "Abort"))
    madname = pvproperty(value="", name=":MADNAME", read_only=True, dtype=ChannelType.STRING)
    statmsg = pvproperty(value="", name=":STATMSG", read_only=True, dtype=ChannelType.STRING)

    def __init__(self, device_name, element_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device_name = device_name
        self.element_name = element_name
        self.saved_bdes = None
        self.bdes_for_undo = None
        initial_value = 0.0
        self.bcon._data["value"] = initial_value
        self.bdes._data["value"] = initial_value
        self.bact._data["value"] = initial_value
        self.madname._data["value"] = element_name.upper()

    @ctrl.putter
    async def ctrl(self, instance, value):
        ioc = instance.group
        if value == "PERTURB":
            await ioc.bact.write(ioc.bdes.value)
        elif value == "TRIM":
            await asyncio.sleep(0.2)
            await ioc.bact.write(ioc.bdes.value)
        elif value == "BCON_TO_BDES":
            await ioc.bdes.write(ioc.bcon.value)
        elif value == "SAVE_BDES":
            self.saved_bdes = ioc.bdes.value
        elif value == "LOAD_BDES":
            if self.saved_bdes:
                await ioc.bdes.write(self.saved_bdes)
        elif value == "UNDO_BDES":
            if self.bdes_for_undo:
                await ioc.bdes.write(self.bdes_for_undo)
        else:
            print("Warning, using a non-implemented magnet control function.")
        return 0

    @pvproperty(
        value=0.0,
        name=":BCTRL",
        upper_ctrl_limit=0.006,
        lower_ctrl_limit=-0.006,
        upper_alarm_limit=0.004,
        lower_alarm_limit=-0.004,
        precision=4,
    )
    async def bctrl(self, instance):
        # We have to do some hacky stuff with caproto private data
        # because otherwise, the putter method gets called any time
        # we read.
        ioc = instance.group
        instance._data["value"] = ioc.bact.value
        return None

    @bctrl.putter
    async def bctrl(self, instance, value):
        ioc = instance.group
        await ioc.bdes.write(value)
        await ioc.ctrl.write("PERTURB")
        return value

    @bdes.putter
    async def bdes(self, instance, value):
        ioc = instance.group
        self.bdes_for_undo = ioc.bdes.value
        return value


def main():
    pvdb = {}
    with open("xcor_list.json") as f:
        mags = json.load(f)
        pvs = [
            MagnetPV(mag["devname"], "XCOR{}".format(mag["devname"].split(":")[-1]), prefix=mag["devname"])
            for mag in mags
        ]
        for pv in pvs:
            pvdb.update(**pv.pvdb)

    _, run_options = ioc_arg_parser(default_prefix="", desc="Simulated Corrector Magnet IOC")
    run(pvdb, **run_options)


if __name__ == "__main__":
    main()
