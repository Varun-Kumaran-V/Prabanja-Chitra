const fs = require('fs');
const path = require('path');

const pagesDir = 'c:\\Users\\varun\\aether-constellation-manager\\src\\pages';
const files = ['Home.jsx', 'MissionControl.jsx', 'Metrics.jsx', 'Comparison.jsx', 'Architecture.jsx'];

files.forEach(file => {
  const filePath = path.join(pagesDir, file);
  if (!fs.existsSync(filePath)) return;
  
  let content = fs.readFileSync(filePath, 'utf8');

  // Fix icon props that were incorrectly written as strings containing JSX
  content = content.replace(/icon="(<span.*?<\/span>)"/g, 'icon={$1}');
  
  fs.writeFileSync(filePath, content);
  console.log(`Updated props in ${file}`);
});
