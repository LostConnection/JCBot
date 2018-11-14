import sc2
from sc2 import run_game, maps, Race, Difficulty, game_info
from sc2.player import Bot, Computer
from sc2.constants import *


class JCBot(sc2.BotAI):

    rampWorker = None
    mainBase = None
    distributed = False

    async def on_step(self, iteration):
        await self.assign_main_base()
        await self.assign_ramp_worker()
        if not self.distributed:
            await self.distribute_workers()
            self.distributed = True
        await self.build_workers()
        await self.build_supply_depots()
        await self.raise_supply_depots_if_enemies_are_near()
        await self.build_barracks()
        await self.build_refineries()

    async def assign_main_base(self):
        if self.mainBase == None:
            self.mainBase = self.units(UnitTypeId.COMMANDCENTER).ready.first

    async def assign_ramp_worker(self):
        if self.rampWorker == None:
            workers = self.workers.gathering
            if workers:  # if workers were found
                self.rampWorker = workers.random
                await self.do(self.rampWorker.move(self.main_base_ramp.barracks_in_middle))

    async def build_workers(self):
        for commandCenter in self.units(UnitTypeId.COMMANDCENTER).ready.noqueue:
            if self.can_afford(UnitTypeId.SCV):
                await self.do(commandCenter.train(UnitTypeId.SCV))

    async def build_supply_depots(self):
        if self.supply_used < 14:
            return
        else:
            depot_placement_positions = self.main_base_ramp.corner_depots
            depots = self.units(UnitTypeId.SUPPLYDEPOT) | self.units(UnitTypeId.SUPPLYDEPOTLOWERED)
            if depots:
                depot_placement_positions = {
                    d for d in depot_placement_positions
                    if depots.closest_distance_to(d) > 1}
            if self.supply_used == 14 and self.supply_left < 5 and self.can_afford(UnitTypeId.SUPPLYDEPOT) and not self.already_pending(UnitTypeId.SUPPLYDEPOT):
                target_depot_location = depot_placement_positions.pop()
                await self.do(self.rampWorker.build(UnitTypeId.SUPPLYDEPOT, target_depot_location))
            if self.supply_left < 5 and not self.supply_used < 16 and self.can_afford(UnitTypeId.SUPPLYDEPOT) and not self.already_pending(UnitTypeId.SUPPLYDEPOT):
                if len(depot_placement_positions) >= 1:
                    target_depot_location = depot_placement_positions.pop()
                    await self.do(self.rampWorker.build(UnitTypeId.SUPPLYDEPOT, target_depot_location))
                else:
                    await self.build(UnitTypeId.SUPPLYDEPOT, near=self.main_base_ramp.corner_depots.pop())

    async def raise_supply_depots_if_enemies_are_near(self):
        for supplyDepot in self.units(UnitTypeId.SUPPLYDEPOT).ready:
            for enemyUnit in self.known_enemy_units.not_structure:
                if enemyUnit.position.to2.distance_to(supplyDepot.position.to2) < 15:
                    break
            else:
                await self.do(supplyDepot(AbilityId.MORPH_SUPPLYDEPOT_LOWER))

    async def build_barracks(self):
        if self.supply_used >= 16 and self.units(UnitTypeId.BARRACKS).empty and self.can_afford(UnitTypeId.BARRACKS):
            target_barracks_location = self.main_base_ramp.barracks_in_middle
            await self.do(self.rampWorker.build(UnitTypeId.BARRACKS, target_barracks_location))

    async def build_refineries(self):
        if self.supply_used >= 16 and self.units(UnitTypeId.REFINERY).empty and self.already_pending(UnitTypeId.REFINERY) < 1:
            vespene = self.state.vespene_geyser.closest_to(self.mainBase)
            if await self.can_place(UnitTypeId.REFINERY, vespene.position) and self.can_afford(UnitTypeId.REFINERY):
                worker = self.select_build_worker(vespene.position, force=True)
                await self.do(worker.build(UnitTypeId.REFINERY, vespene))





run_game(maps.get("(2)16-BitLE"), [
    Bot(Race.Terran, JCBot()),
    Computer(Race.Terran, Difficulty.Easy)
], realtime=True)
