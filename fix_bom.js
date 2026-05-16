const fs = require('fs');

const files = [
  'D:/work/agentV1/rag-qa-frontend/src/views/Dashboard.vue',
  'D:/work/agentV1/rag-qa-frontend/src/views/QA.vue',
  'D:/work/agentV1/rag-qa-frontend/src/views/Layout.vue',
  'D:/work/agentV1/rag-qa-frontend/src/views/Login.vue',
  'D:/work/agentV1/rag-qa-frontend/src/views/Knowledge.vue',
  'D:/work/agentV1/rag-qa-frontend/src/views/Documents.vue',
  'D:/work/agentV1/rag-qa-frontend/src/views/System.vue',
  'D:/work/agentV1/rag-qa-frontend/src/router/index.ts',
  'D:/work/agentV1/rag-qa-frontend/index.html'
];

files.forEach(filePath => {
  // Read raw bytes
  const buf = fs.readFileSync(filePath);
  
  // Remove any existing BOMs
  let start = 0;
  while (buf[start] === 0xEF && buf[start+1] === 0xBB && buf[start+2] === 0xBF) {
    start += 3;
  }
  
  // Get content without BOM
  const content = buf.slice(start).toString('utf8');
  
  // Write with single UTF-8 BOM
  const bom = Buffer.from([0xEF, 0xBB, 0xBF]);
  const contentBuf = Buffer.from(content, 'utf8');
  fs.writeFileSync(filePath, Buffer.concat([bom, contentBuf]));
  
  console.log('Fixed: ' + filePath.split('/').pop());
});
