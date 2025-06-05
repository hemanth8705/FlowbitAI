import { useState } from "react";
import "./App.css";

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [responseData, setResponseData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
    setResponseData(null);
    setErrorMsg("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!selectedFile) {
      setErrorMsg("Please choose a file");
      return;
    }

    setLoading(true);
    setErrorMsg("");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await fetch("http://127.0.0.1:8000/process", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        throw new Error(`HTTP error! Status ${res.status}`);
      }
      const data = await res.json();
      setResponseData(data);
    } catch (err) {
      console.error("Error processing file:", err);
      setErrorMsg("Error processing file. " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Flowbit AI Document Processor</h1>
      <form onSubmit={handleSubmit} className="upload-form">
        <input
          type="file"
          onChange={handleFileChange}
          accept=".txt,.json,.pdf"
        />
        <button type="submit" disabled={loading}>
          {loading ? "Processing File..." : "Upload and Process"}
        </button>
      </form>
      {errorMsg && <p className="error">{errorMsg}</p>}
      {responseData && (
        <div className="response">
          <h2>Processing Results</h2>
          <div className="result-section">
            <strong>Run ID:</strong> {responseData.run_id}
          </div>
          <div className="result-section">
            <strong>Classification:</strong>
            <pre>{JSON.stringify(responseData.classification, null, 2)}</pre>
          </div>
          <div className="result-section">
            <strong>Agent Result:</strong>
            <pre>{JSON.stringify(responseData.agent_result, null, 2)}</pre>
          </div>
          <div className="result-section">
            <strong>Action Response:</strong>
            <pre>{JSON.stringify(responseData.action_response, null, 2)}</pre>
          </div>
          <div className="result-section">
            <strong>Extracted Text:</strong>
            <pre>{responseData.extracted_text}</pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;