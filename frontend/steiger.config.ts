import fsd from "@feature-sliced/steiger-plugin";
import { defineConfig } from "steiger";

// PLAN-22 DP-4: VER-17 se cierra con Steiger, el linter oficial de FSD v2.1 (A-09).
export default defineConfig([...fsd.configs.recommended]);
