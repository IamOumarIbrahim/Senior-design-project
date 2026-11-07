//   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
//        Oumar Mamoun Ibrahim U22200741
//        Abdullah Jafar Abdelhamid U23101327
//        Faris Munadhil Ahmed Alagha U23104246
//        Mohamed Ahmed Saad Khafagy U20101649

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000"
    }
  }
});
