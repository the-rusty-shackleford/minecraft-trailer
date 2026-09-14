/*
 * The Trailer - a livestock trailer for Vanilla Wheels.
 * Copyright (C) 2026 Rusty Shackleford and nfx
 *
 * This program is free software: you can redistribute it and/or modify it
 * under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or (at your
 * option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License
 * for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <https://www.gnu.org/licenses/>.
 */
package com.chunkworks.trailer.gametest;

import com.chunkworks.vanillawheels.ModContent;
import com.chunkworks.vanillawheels.Vehicle;
import com.chunkworks.vanillawheels.api.VanillaWheels;
import com.chunkworks.vanillawheels.api.VehicleProfile;
import com.chunkworks.vanillawheels.domain.Input;
import com.chunkworks.vanillawheels.domain.Tow;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.core.NonNullList;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.animal.Cow;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/**
 * The Trailer on a headless server: its profile is a trailer -- no engine,
 * no seats, a tongue, two wheels, room for four grown animals or eight
 * young, two doors; the Trailblazer catches its tongue and tows it
 * straight and round a turn; four cows board through open doors and a
 * fifth is refused, calves at a half each; the chassis crafts from six
 * steel blocks and three iron bars.
 */
@GameTestHolder("trailer")
@PrefixGameTestTemplate(false)
public final class TrailerGameTests {
    private static final int LENGTH = 48;
    private static final int WIDTH = 15;
    private static final int FLOOR = 4;
    private static final ResourceLocation TRAILER = ResourceLocation.fromNamespaceAndPath("trailer", "trailer");
    private static final ResourceLocation TRUCK = ResourceLocation.fromNamespaceAndPath("trailblazer", "trailblazer");
    private static final Input GAS = new Input(1, 0, false, true, true);
    private static final Input GAS_RIGHT = new Input(1, 1, false, true, true);

    public TrailerGameTests() {}

    private static void layFloor(GameTestHelper helper) {
        for (int x = 0; x < LENGTH; x++) {
            for (int z = 0; z < WIDTH; z++) {
                for (int y = 0; y < FLOOR; y++) {
                    helper.setBlock(new BlockPos(x, y, z), Blocks.DIRT);
                }
            }
        }
    }

    private static Vehicle spawn(GameTestHelper helper, ResourceLocation id, double x, double z, float yaw) {
        Vehicle v = Vehicle.create(helper.getLevel(), id, helper.absoluteVec(new Vec3(x, FLOOR, z)), yaw);
        helper.assertTrue(v != null, id + " is registered");
        if (v.profile().engine().isPresent()) {
            v.setFuel(v.tank().capacity());
        }
        helper.getLevel().addFreshEntity(v);
        return v;
    }

    private static double yawGap(Vehicle a, Vehicle b) {
        return Math.abs(Math.toDegrees(Tow.wrap(Math.toRadians(a.getYRot() - b.getYRot()))));
    }

    private static Cow cow(GameTestHelper helper, double x, double z, boolean baby) {
        Cow cow = EntityType.COW.create(helper.getLevel());
        Vec3 at = helper.absoluteVec(new Vec3(x, FLOOR, z));
        cow.setPos(at.x, at.y, at.z);
        cow.setNoAi(true);
        cow.setBaby(baby);
        helper.getLevel().addFreshEntity(cow);
        return cow;
    }

    @GameTest(template = "arena", timeoutTicks = 60)
    public void theProfileIsATrailer(GameTestHelper helper) {
        Optional<VehicleProfile> p = VanillaWheels.profile(helper.getLevel().registryAccess(), TRAILER).map(h -> h.value());
        helper.assertTrue(p.isPresent(), "trailer:trailer is in the vehicle registry");
        VehicleProfile t = p.get();
        helper.assertTrue(t.engine().isEmpty(), "no engine");
        helper.assertTrue(t.seats().isEmpty(), "no seats");
        helper.assertTrue(t.hitch().front().isPresent(), "a tongue");
        helper.assertTrue(t.hitch().rear().isEmpty(), "no rear hitch");
        helper.assertValueEqual(t.wheels().positions().size(), 2, "two wheels");
        helper.assertValueEqual(t.cargo().map(VehicleProfile.Cargo::adults).orElse(0), 4, "four adults");
        helper.assertValueEqual(t.cargo().map(VehicleProfile.Cargo::young).orElse(0), 8, "eight young");
        helper.assertValueEqual(t.doors().size(), 2, "two doors");
        helper.assertTrue(t.handedness() == VehicleProfile.Handedness.RIGHT, "right-handed");
        Vehicle v = spawn(helper, TRAILER, 7.5, 7.5, 0.0f);
        helper.assertTrue(v.hasTongue(), "the entity has a tongue");
        helper.assertTrue(v.tongue().z - v.getZ() > 2.5, "the tongue is ahead of it: " + (v.tongue().z - v.getZ()));
        helper.assertTrue(v.getName().getString().equals("Trailer"), "named: " + v.getName().getString());
        helper.succeed();
    }

    @GameTest(template = "runway", timeoutTicks = 200)
    public void theTrailblazerCatchesTheTongueAndTowsItStraightAndRoundATurn(GameTestHelper helper) {
        layFloor(helper);
        Vehicle truck = spawn(helper, TRUCK, 12.5, 7.5, -90.0f);
        // The trailer sits so its tongue is a third of a block short of the truck's hitch ball, wherever the two profiles put them.
        Vehicle trailer = spawn(helper, TRAILER, 6.0, 7.5, -90.0f);
        trailer.setPos(trailer.getX() - (trailer.tongue().x - truck.hitchPoint().x) - 0.3, trailer.getY(), trailer.getZ());
        double x0 = trailer.getX();
        truck.setScriptedInput(GAS);
        helper.runAtTickTime(50, () -> {
            helper.assertTrue(trailer.tower() == truck, "hitched: " + trailer.tower());
            helper.assertTrue(trailer.getX() - x0 > 5.0, "the trailer came along: " + (trailer.getX() - x0));
            helper.assertTrue(yawGap(truck, trailer) < 3.0, "straight behind: " + yawGap(truck, trailer));
            helper.assertTrue(trailer.tongue().distanceTo(truck.hitchPoint()) < 0.3, "the tongue is on the hitch: " + trailer.tongue().distanceTo(truck.hitchPoint()));
            truck.setScriptedInput(GAS_RIGHT);
        });
        helper.runAtTickTime(65, () -> {
            double gap = yawGap(truck, trailer);
            helper.assertTrue(gap > 3.0 && gap < 60.0, "in the turn the trailer lags: " + gap);
            helper.assertTrue(trailer.tongue().distanceTo(truck.hitchPoint()) < 0.3, "still on the hitch");
            truck.setScriptedInput(null);
            helper.succeed();
        });
    }

    @GameTest(template = "runway", timeoutTicks = 100)
    public void fourCowsBoardAFifthIsRefusedAndCalvesTakeAHalf(GameTestHelper helper) {
        layFloor(helper);
        Vehicle trailer = spawn(helper, TRAILER, 20.5, 7.5, -90.0f);
        Player p = helper.makeMockPlayer(GameType.SURVIVAL);
        Vec3 at = helper.absoluteVec(new Vec3(14.5, FLOOR, 7.5));
        p.setPos(at.x, at.y, at.z);
        List<Cow> herd = new ArrayList<>();
        for (int i = 0; i < 5; i++) {
            herd.add(cow(helper, 13.5, 3.5 + i * 2, false));
        }
        for (Cow c : herd) {
            c.setLeashedTo(p, true);
        }
        trailer.toggleDoors();
        p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.LEAD));
        helper.assertTrue(trailer.interact(p, InteractionHand.MAIN_HAND).consumesAction(), "the lead click was taken");
        helper.assertValueEqual(trailer.animals().size(), 4, "four cows aboard");
        helper.assertValueEqual((int) herd.stream().filter(c -> c.getLeashHolder() == p).count(), 1, "the fifth stays on the lead");
        helper.assertTrue(!trailer.cargo().accepts(true), "not even a calf fits now");
        trailer.ejectPassengers();
        for (Cow c : herd) {
            c.dropLeash(true, false);
            c.discard();
        }
        Cow calf = cow(helper, 13.5, 12.5, true);
        calf.setLeashedTo(p, true);
        helper.assertTrue(trailer.interact(p, InteractionHand.MAIN_HAND).consumesAction(), "the lead click was taken again");
        helper.assertValueEqual(trailer.cargo().young(), 1, "a calf aboard");
        helper.assertTrue(Math.abs(trailer.cargo().fraction() - 0.125) < 1e-9, "at an eighth of the room: " + trailer.cargo().fraction());
        helper.succeed();
    }

    @GameTest(template = "arena", timeoutTicks = 60)
    public void theChassisCraftsFromSteelBlocksAndIronBars(GameTestHelper helper) {
        NonNullList<ItemStack> grid = NonNullList.withSize(9, ItemStack.EMPTY);
        var steelBlock = net.minecraft.core.registries.BuiltInRegistries.ITEM.get(ResourceLocation.fromNamespaceAndPath("metalsandmaterials", "steel_block"));
        helper.assertTrue(steelBlock != Items.AIR, "Metals and Materials' steel block is here");
        int[] bars = {1, 6, 7, 8};
        for (int i = 0; i < 9; i++) {
            boolean bar = false;
            for (int b : bars) {
                bar |= b == i;
            }
            grid.set(i, new ItemStack(bar ? Items.IRON_BARS : steelBlock));
        }
        CraftingInput input = CraftingInput.of(3, 3, grid);
        Optional<RecipeHolder<CraftingRecipe>> recipe = helper.getLevel().getRecipeManager().getRecipeFor(RecipeType.CRAFTING, input, helper.getLevel());
        helper.assertTrue(recipe.isPresent(), "the grid crafts something");
        helper.assertValueEqual(recipe.get().id(), ResourceLocation.fromNamespaceAndPath("trailer", "trailer_chassis"), "the Trailer's chassis recipe");
        ItemStack result = recipe.get().value().assemble(input, helper.getLevel().registryAccess());
        helper.assertTrue(result.is(ModContent.CHASSIS.get()), "a chassis: " + result);
        helper.assertValueEqual(VanillaWheels.vehicleOf(result).orElse(null), TRAILER, "for the Trailer");
        helper.succeed();
    }
}
