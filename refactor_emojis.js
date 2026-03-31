const fs = require('fs');
const path = require('path');

const pagesDir = 'c:\\Users\\varun\\aether-constellation-manager\\src\\pages';
const files = ['Home.jsx', 'MissionControl.jsx', 'Metrics.jsx', 'Comparison.jsx', 'Architecture.jsx'];

files.forEach(file => {
  const filePath = path.join(pagesDir, file);
  if (!fs.existsSync(filePath)) return;
  
  let content = fs.readFileSync(filePath, 'utf8');

  // Replace remaining emojis 
  content = content.replace(/🚀/g, '<span className="material-symbols-outlined inline-block align-middle">rocket_launch</span>');
  content = content.replace(/⏳/g, '<span className="material-symbols-outlined inline-block align-middle">hourglass_empty</span>');
  content = content.replace(/⚠️/g, '<span className="material-symbols-outlined">error</span>');
  
  fs.writeFileSync(filePath, content);
  console.log(`Updated emojis in ${file}`);
});
