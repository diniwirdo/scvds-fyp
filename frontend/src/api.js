const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Upload failed");
  }

  return response.json();
}

export async function analyzeContract(contractId) {
  const response = await fetch(`${API_URL}/analyze/${contractId}`, {
    method: "POST",
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Analysis failed");
  }

  return response.json();
}

export async function getResults(contractId) {
  const response = await fetch(`${API_URL}/results/${contractId}`);
  return response.json();
}

export async function getHistory() {
  const response = await fetch(`${API_URL}/history`);
  return response.json();
}