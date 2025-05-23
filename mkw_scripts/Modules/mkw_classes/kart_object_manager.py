from dolphin import memory # type: ignore
from mkw_scripts.Modules import mkw_config

from . import RegionError

class KartObjectManager:
    @staticmethod
    def chain() -> int:
        try:
            address = {"RMCE01": 0x809BD110, "RMCP01": 0x809C18F8,
                    "RMCJ01": 0x809C0958, "RMCK01": 0x809AFF38}
            return memory.read_u32(address[mkw_config.game_id_string])
        except KeyError:
            raise RegionError

    @staticmethod
    def kart_object_arr() -> int:
        kart_obj_mgr_ref = KartObjectManager.chain()
        return memory.read_u32(kart_obj_mgr_ref + 0x20)

    @staticmethod
    def kart_object(player_idx=0) -> int:
        assert(0 <= player_idx < KartObjectManager.player_count())
        kart_obj_arr_ref = KartObjectManager.kart_object_arr()
        kart_obj_ptr = kart_obj_arr_ref + (player_idx * 0x4)
        return memory.read_u32(kart_obj_ptr)

    @staticmethod
    def player_count() -> int:
        """This is copied from RaceConfig->mRaceScenario.mPlayerCount."""
        return memory.read_u8(KartObjectManager.chain() + 0x24)

    @staticmethod
    def flags() -> int:
        kart_obj_mgr_ref = KartObjectManager.chain()
        flags_ref = kart_obj_mgr_ref + 0x28
        return memory.read_u32(flags_ref)