const fs = require('fs');
const path = require('path');

const pagesDir = 'c:\\Users\\varun\\aether-constellation-manager\\src\\pages';
const files = ['Home.jsx', 'MissionControl.jsx', 'Metrics.jsx', 'Comparison.jsx', 'Architecture.jsx'];

files.forEach(file => {
  const filePath = path.join(pagesDir, file);
  if (!fs.existsSync(filePath)) return;
  
  let content = fs.readFileSync(filePath, 'utf8');

  // Spacing improvements
  content = content.replace(/\bpx-6\b/g, 'px-8');
  content = content.replace(/\bgap-4\b/g, 'gap-6');
  content = content.replace(/\bmb-6\b/g, 'mb-10');

  // Emoji replacements with custom rules
  
  // Specific prop replacements for EmptyState / StatCard / CapabilityCard etc.
  content = content.replace(/icon="✓"/g, 'icon={<span className="material-symbols-outlined text-4xl">check_circle</span>}');
  content = content.replace(/icon="⚠️"/g, 'icon={<span className="material-symbols-outlined text-4xl">error</span>}');
  content = content.replace(/icon="📋"/g, 'icon={<span className="material-symbols-outlined text-4xl">list_alt</span>}');
  content = content.replace(/icon="📅"/g, 'icon={<span className="material-symbols-outlined text-4xl">calendar_month</span>}');
  content = content.replace(/icon="🛰️"/g, 'icon={<span className="material-symbols-outlined text-4xl">satellite</span>}');
  content = content.replace(/icon="⛽"/g, 'icon={<span className="material-symbols-outlined text-4xl">local_gas_station</span>}');

  // Dictionary inside MissionControl.jsx
  content = content.replace(/icon: '✓'/g, 'icon: \'check_circle\'');
  content = content.replace(/icon: '⏸'/g, 'icon: \'pause_circle\'');
  content = content.replace(/icon: '⊘'/g, 'icon: \'cancel\''); // This will need the span wrapper in code, but let's see. Actually, let's replace the whole object values with JSX.
  content = content.replace(/icon: 'check_circle'/g, 'icon: <span className="material-symbols-outlined">check_circle</span>');
  content = content.replace(/icon: 'pause_circle'/g, 'icon: <span className="material-symbols-outlined">pause_circle</span>');
  content = content.replace(/icon: 'cancel'/g, 'icon: <span className="material-symbols-outlined">cancel</span>');

  // Direct text replacements
  content = content.replace(/🚨/g, '<span className="material-symbols-outlined">warning</span>');
  content = content.replace(/⚠️/g, '<span className="material-symbols-outlined">error</span>');
  content = content.replace(/⚠/g, '<span className="material-symbols-outlined">warning</span>');
  content = content.replace(/🧠/g, '<span className="material-symbols-outlined inline-block align-middle">insights</span>');
  content = content.replace(/>✓</g, '><span className="material-symbols-outlined">check_circle</span><');
  content = content.replace(/✓ All satellites protected/g, '<span className="material-symbols-outlined inline-block align-middle text-sm mr-1">check_circle</span> All satellites protected');
  
  content = content.replace(/>⛽</g, '><span className="material-symbols-outlined">local_gas_station</span><');
  content = content.replace(/>📋</g, '><span className="material-symbols-outlined">list_alt</span><');

  // Specific text block in MissionControl
  content = content.replace(/🧠 LAST DECISION/g, '<span className="material-symbols-outlined mr-2">insights</span> LAST DECISION');

  fs.writeFileSync(filePath, content);
  console.log(`Updated ${file}`);
});
