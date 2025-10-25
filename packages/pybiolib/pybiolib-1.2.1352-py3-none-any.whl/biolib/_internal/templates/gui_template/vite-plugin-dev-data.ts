import { Plugin } from 'vite';
import fs from 'fs';
import path from 'path';

export function devDataPlugin(): Plugin {
  let isDev = false;
  
  return {
    name: 'dev-data-plugin',
    configResolved(config) {
      isDev = config.mode === 'development';
    },
    transform(code: string, id: string) {
      if (id.endsWith('biolib-sdk.ts')) {
        let injectedCode: string;
        
        if (isDev) {
          const devDataDir = path.join(__dirname, 'dev-data');
          const devDataMap: Record<string, string> = {};
          
          if (fs.existsSync(devDataDir)) {
            const files = fs.readdirSync(devDataDir);
            for (const file of files) {
              const filePath = path.join(devDataDir, file);
              if (fs.statSync(filePath).isFile()) {
                const content = fs.readFileSync(filePath);
                const base64Content = content.toString('base64');
                devDataMap[file] = base64Content;
              }
            }
          }
          
          const devDataJson = JSON.stringify(devDataMap);
          injectedCode = code.replace(
            '/* DEV_DATA_INJECTION */',
            `const DEV_DATA_FILES: Record<string, string> = ${devDataJson};`
          );
        } else {
          injectedCode = code.replace(
            '/* DEV_DATA_INJECTION */',
            '// Dev data not included in production build'
          );
        }
        
        return {
          code: injectedCode,
          map: null
        };
      }
    }
  };
}
