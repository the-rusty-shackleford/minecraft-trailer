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

import com.chunkworks.vanillawheels.Vehicle;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.animal.Cow;
import com.mojang.blaze3d.platform.NativeImage;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.function.Consumer;
import java.util.function.IntPredicate;
import java.util.function.Supplier;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Difficulty;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.LevelSettings;
import net.minecraft.world.level.WorldDataConfiguration;
import net.minecraft.world.level.levelgen.WorldOptions;
import net.minecraft.world.level.levelgen.presets.WorldPresets;
import net.minecraft.world.phys.Vec3;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * The Trailer on film: a flat world, the trailer a few blocks ahead of the
 * player, side on and unhitched; then hitched behind a Trailblazer with
 * its doors swung open and two cows aboard, seen from behind and to the
 * side so the doors and the cows show. One {@code booth: PASS} or
 * {@code booth: FAIL} line per check; the Gradle task reads them. Client
 * only, active only under {@code trailer.photobooth}.
 */
@EventBusSubscriber(modid = GameTestMod.MOD_ID, value = Dist.CLIENT)
public final class TrailerBooth {
    private TrailerBooth() {}

    private static final Logger LOG = LoggerFactory.getLogger("Trailer booth");
    private static final boolean ACTIVE = Boolean.getBoolean("trailer.photobooth");
    private static final ResourceLocation TRUCK = ResourceLocation.fromNamespaceAndPath("trailblazer", "trailblazer");
    private static final ResourceLocation TRAILER = ResourceLocation.fromNamespaceAndPath("trailer", "trailer");

    private enum Phase { TITLE, LOADING, PLACING, RUNNING, DONE }

    private record Step(int at, Runnable action) {}

    /** Ticks for the world to settle after loading, and between a change and its photo. */
    private static final int HOLD = 100;
    private static final int SETTLE = 60;
    /** Where the player stands; the car sits AHEAD blocks south of it. */
    private static final double X = 0.5;
    private static final double Z = 0.5;
    private static final double AHEAD = 9.0;

    private static Phase phase = Phase.TITLE;
    private static int tick = 0;
    private static List<Step> steps;
    private static UUID car;
    private static UUID trailerId;

    @SubscribeEvent
    public static void onClientTick(ClientTickEvent.Post event) {
        if (!ACTIVE) {
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        switch (phase) {
            case TITLE -> {
                if (mc.screen instanceof TitleScreen && mc.getOverlay() == null) {
                    phase = Phase.LOADING;
                    createWorld(mc);
                }
            }
            case LOADING -> {
                MinecraftServer server = mc.getSingleplayerServer();
                if (mc.level != null && mc.player != null && mc.screen == null && server != null
                        && mc.level.hasChunkAt(mc.player.blockPosition())) {
                    phase = Phase.PLACING;
                    // No HUD: the crosshair, inverted over a dark body, reads as a lit lamp.
                    mc.options.hideGui = true;
                    steps = plan(mc);
                    onServer(mc, TrailerBooth::setUp);
                }
            }
            case PLACING -> {
                // The count starts once the client has the player on the mark and the car in view:
                // on a slow renderer the teleport and the spawn land some frames after they are sent.
                if (mc.player != null && mc.player.onGround() && mc.player.distanceToSqr(X, mc.player.getY(), Z) < 0.25 && carId(mc) != -1) {
                    phase = Phase.RUNNING;
                    tick = 0;
                }
            }
            case RUNNING -> {
                for (Step step : steps) {
                    if (step.at() == tick) {
                        step.action().run();
                    }
                }
                tick++;
            }
            case DONE -> { }
        }
    }

    private static void createWorld(Minecraft mc) {
        GameRules rules = new GameRules();
        rules.getRule(GameRules.RULE_WEATHER_CYCLE).set(false, null);
        rules.getRule(GameRules.RULE_DAYLIGHT).set(false, null);
        rules.getRule(GameRules.RULE_DOMOBSPAWNING).set(false, null);
        LevelSettings settings = new LevelSettings("Trailer booth", GameType.CREATIVE, false, Difficulty.PEACEFUL,
                true, rules, WorldDataConfiguration.DEFAULT);
        WorldOptions options = new WorldOptions(1L, false, false);
        mc.createWorldOpenFlows().createFreshLevel("trailer-booth", settings, options,
                registries -> registries.registryOrThrow(Registries.WORLD_PRESET).getHolderOrThrow(WorldPresets.FLAT)
                        .value().createWorldDimensions(),
                mc.screen);
    }

    /** Noon; the player on the grass facing south; the trailer ahead, side on, facing east. */
    private static void setUp(ServerPlayer sp) {
        ServerLevel level = sp.serverLevel();
        level.setDayTime(6000L);
        sp.getAbilities().flying = false;
        sp.onUpdateAbilities();
        double y = level.getMinBuildHeight() + 5;
        sp.teleportTo(level, X, y, Z, 0.0f, 8.0f);
        sp.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
        sp.setItemInHand(InteractionHand.OFF_HAND, ItemStack.EMPTY);
        Vehicle v = Vehicle.create(level, TRAILER, new Vec3(X, y, Z + AHEAD), -90.0f);
        if (v == null) {
            LOG.error("booth: FAIL the Trailer profile is registered -- Vehicle.create returned null");
            return;
        }
        level.addFreshEntity(v);
        car = v.getUUID();
    }

    private static List<Step> plan(Minecraft mc) {
        List<Step> s = new ArrayList<>();
        int t = HOLD;
        s.add(new Step(t, () -> {
            int body = count(mc, TrailerBooth::pale);
            shoot(mc, "booth-side");
            verdict("the trailer's side shows its pale body", () -> body > 1500 ? null : "pale pixels " + body);
        }));
        // Hitched behind a Trailblazer, doors open, two cows aboard; the camera behind and to the left, up a little.
        s.add(new Step(t += 2, () -> onServer(mc, sp -> {
            ServerLevel level = sp.serverLevel();
            double y = level.getMinBuildHeight() + 5;
            if (level.getEntity(car) instanceof Vehicle old) {
                old.discard();
            }
            double x = X + 20.0;
            Vehicle truck = Vehicle.create(level, TRUCK, new Vec3(x + 2.0, y, Z + 8.0), 0.0f);
            Vehicle trailer = Vehicle.create(level, TRAILER, new Vec3(x + 2.0, y, Z + 8.0 - 42 / 16.0 - 2.6), 0.0f);
            if (truck == null || trailer == null) {
                LOG.error("booth: FAIL the Trailblazer and the Trailer are registered");
                return;
            }
            level.addFreshEntity(truck);
            level.addFreshEntity(trailer);
            truck.hitch(trailer);
            trailer.toggleDoors();
            for (int i = 0; i < 2; i++) {
                Cow cow = EntityType.COW.create(level);
                if (cow != null) {
                    cow.setPos(trailer.getX(), trailer.getY(), trailer.getZ());
                    cow.setNoAi(true);
                    level.addFreshEntity(cow);
                    if (!cow.startRiding(trailer, true)) {
                        LOG.error("booth: FAIL a cow boards the trailer");
                    }
                }
            }
            trailerId = trailer.getUUID();
            sp.getAbilities().flying = true;
            sp.onUpdateAbilities();
            sp.teleportTo(level, x + 6.0, y + 2.5, Z - 1.5, 42.0f, 20.0f);
        })));
        s.add(new Step(t += SETTLE, () -> {
            Vehicle found = null;
            if (mc.level != null) {
                for (var e : mc.level.entitiesForRendering()) {
                    if (e instanceof Vehicle v && e.getUUID().equals(trailerId)) {
                        found = v;
                    }
                }
            }
            Vehicle trailer = found;
            shoot(mc, "booth-hitched");
            verdict("the client sees the trailer hitched to the truck", () -> trailer != null && trailer.tower() != null ? null : "trailer " + trailer + ", tower " + (trailer == null ? null : trailer.tower()));
            verdict("its doors are swung open", () -> trailer != null && trailer.doorSwing(1.0f) > 0.9f ? null : "swing " + (trailer == null ? null : trailer.doorSwing(1.0f)));
            verdict("with two cows aboard", () -> trailer != null && trailer.animals().size() == 2 ? null : "animals " + (trailer == null ? null : trailer.animals()));
        }));
        s.add(new Step(t += 20, () -> {
            LOG.info("booth: PASS all checks ran");
            phase = Phase.DONE;
            mc.stop();
        }));
        return s;
    }

    private static int carId(Minecraft mc) {
        if (mc.level == null) {
            return -1;
        }
        for (var e : mc.level.entitiesForRendering()) {
            if (e instanceof Vehicle && e.getUUID().equals(car)) {
                return e.getId();
            }
        }
        return -1;
    }

    // --- reading the frame -----------------------------------------------

    /** The body swatches under white dye: a pale, even grey, which neither grass nor sky is. */
    private static boolean pale(int rgb) {
        int r = rgb >> 16 & 0xFF, g = rgb >> 8 & 0xFF, b = rgb & 0xFF;
        return r > 140 && g > 140 && b > 140 && Math.abs(r - g) < 16 && Math.abs(g - b) < 16;
    }

    /**
     * effects: returns how many pixels of the frame's middle satisfy
     * {@code test} (rgb, no alpha): rows 36..70 % and columns 20..80 %,
     * which is below the sky and above the hotbar and the hand, and where
     * every shot puts the car
     */
    private static int count(Minecraft mc, IntPredicate test) {
        return countIn(mc, test, 0.36, 0.70);
    }

    /** effects: returns how many pixels between the given height fractions, columns 20..80 %, satisfy {@code test} */
    private static int countIn(Minecraft mc, IntPredicate test, double top, double bottom) {
        try (NativeImage image = Screenshot.takeScreenshot(mc.getMainRenderTarget())) {
            int n = 0;
            int w = image.getWidth();
            int h = image.getHeight();
            for (int y = (int) (h * top); y < (int) (h * bottom); y++) {
                for (int x = (int) (w * 0.2); x < (int) (w * 0.8); x++) {
                    int abgr = image.getPixelRGBA(x, y);
                    int rgb = (abgr & 0xFF) << 16 | (abgr >> 8 & 0xFF) << 8 | (abgr >> 16 & 0xFF);
                    if (test.test(rgb)) {
                        n++;
                    }
                }
            }
            return n;
        }
    }

    // --- plumbing --------------------------------------------------------

    private static void onServer(Minecraft mc, Consumer<ServerPlayer> action) {
        MinecraftServer server = mc.getSingleplayerServer();
        if (server == null || mc.player == null) {
            return;
        }
        server.execute(() -> {
            ServerPlayer sp = server.getPlayerList().getPlayer(mc.player.getUUID());
            if (sp != null) {
                action.accept(sp);
            }
        });
    }

    private static void withCar(Minecraft mc, Consumer<Vehicle> action) {
        onServer(mc, sp -> {
            if (sp.serverLevel().getEntity(car) instanceof Vehicle v) {
                action.accept(v);
            } else {
                LOG.error("booth: FAIL the car is in the level -- gone");
            }
        });
    }

    private static void shoot(Minecraft mc, String name) {
        Screenshot.grab(mc.gameDirectory, name + ".png", mc.getMainRenderTarget(),
                message -> LOG.info("booth: {}", message.getString()));
    }

    /** Runs {@code check}; null is a pass, anything else the failure's detail. */
    private static void verdict(String what, Supplier<String> check) {
        String detail;
        try {
            detail = check.get();
        } catch (RuntimeException e) {
            detail = e.toString();
        }
        if (detail == null) {
            LOG.info("booth: PASS {}", what);
        } else {
            LOG.error("booth: FAIL {} -- {}", what, detail);
        }
    }
}
