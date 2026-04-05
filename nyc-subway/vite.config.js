// import { defineConfig } from 'vite'
// import vue from '@vitejs/plugin-vue'

// // https://vite.dev/config/
// export default defineConfig({
//   plugins: [vue()],
// })
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  // 1. 设置基础路径为相对路径
  base: './', 
  build: {
    // 2. 将打包输出目录改为 docs（默认是 dist）
    outDir: 'docs' 
  }
})