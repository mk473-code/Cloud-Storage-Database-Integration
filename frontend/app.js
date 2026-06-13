// ──────────────────────────────────────────────
//  REPLACE these two URLs after deploying to AWS
// ──────────────────────────────────────────────
const SAVE_API = "https://0ifivga2q5.execute-api.eu-north-1.amazonaws.com/save";
const FILES_API = "https://0ifivga2q5.execute-api.eu-north-1.amazonaws.com/files";

// ── Upload Flow ────────────────────────────────
async function uploadFile() {
  const fileName   = document.getElementById('fileName').value.trim();
  const description = document.getElementById('description').value.trim();
  const fileInput  = document.getElementById('fileInput');
  const file       = fileInput.files[0];
  const btn        = document.getElementById('uploadBtn');
  const statusMsg  = document.getElementById('statusMsg');

  // Basic validation
  if (!fileName || !description || !file) {
    showStatus('Please fill in all fields and choose a file.', 'error');
    return;
  }

  // Block files larger than 10MB
  if (file.size > 10 * 1024 * 1024) {
    showStatus('❌ File too large. Maximum size is 10MB.', 'error');
    return;
  }

  btn.disabled = true;
  showStatus('⏳ Uploading…', '');

  try {
    // Step 1 – Ask Lambda for a pre-signed S3 URL & save metadata
    const metaRes = await fetch(SAVE_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fileName, description, fileType: file.type })
    });
    const metaData = await metaRes.json();
    if (!metaRes.ok) throw new Error(metaData.error || 'Metadata save failed');

    // Step 2 – Validate the pre-signed URL is an AWS S3 domain before using it (prevents SSRF)
    const allowedS3Host = /^https:\/\/[\w.-]+\.s3\.amazonaws\.com\/|^https:\/\/s3\.amazonaws\.com\//;
    if (!allowedS3Host.test(metaData.presignedUrl)) {
      throw new Error('Invalid upload URL received from server.');
    }

    const fileType = file.type || 'application/octet-stream';
    const s3Res = await fetch(metaData.presignedUrl, {
      method: 'PUT',
      headers: { 'Content-Type': fileType },
      body: file
    });
    if (!s3Res.ok) throw new Error('S3 upload failed. Check bucket CORS settings.');

    showStatus('✅ File uploaded successfully!', 'success');
    clearForm();
    await loadFiles();           // Refresh table

  } catch (err) {
    showStatus(`❌ Error: ${err.message}`, 'error');
  } finally {
    btn.disabled = false;
  }
}

// ── Load Files Table ───────────────────────────
async function loadFiles() {
  const tbody = document.getElementById('tableBody');
  tbody.innerHTML = '<tr><td colspan="5" class="empty">Loading…</td></tr>';

  try {
    const res = await fetch(FILES_API);
    const data = await res.json();

    if (!data.files || data.files.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty">No files yet. Upload one above!</td></tr>';
      return;
    }

    tbody.innerHTML = data.files.map((f, i) => `
      <tr>
        <td>${i + 1}</td>
        <td>${escHtml(f.fileName)}</td>
        <td>${escHtml(f.description)}</td>
        <td>${escHtml(f.uploadDate)}</td>
        <td><a class="file-link" href="${f.fileUrl}" target="_blank">View ↗</a></td>
      </tr>`).join('');

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty error">Failed to load files: ${err.message}</td></tr>`;
  }
}

// ── Helpers ────────────────────────────────────
function showStatus(msg, type) {
  const el = document.getElementById('statusMsg');
  el.textContent = msg;
  el.className = `status-msg ${type}`;
}

function clearForm() {
  document.getElementById('fileName').value  = '';
  document.getElementById('description').value = '';
  document.getElementById('fileInput').value  = '';
}

// Prevent XSS when injecting user data into the DOM
function escHtml(str) {
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(str || ''));
  return d.innerHTML;
}

// ── Auto-load on page open ─────────────────────
window.addEventListener('DOMContentLoaded', loadFiles);
