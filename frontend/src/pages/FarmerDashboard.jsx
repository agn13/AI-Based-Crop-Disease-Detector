import { useState } from "react";

export default function FarmerDashboard() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const handleFileChange = (event) => {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    setError("");
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError("Please choose an image first.");
      return;
    }

    setIsUploading(true);
    setError("");
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch("/api/predict", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        const message = data.error || data.detail || "Prediction request failed.";
        throw new Error(message);
      }

      setResult(data);
    } catch (uploadError) {
      setError(uploadError.message || "Unable to process request.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-green-50 flex flex-col items-center justify-center p-4">
      <h1 className="text-3xl font-bold text-green-700 mb-6 text-center">
        Crop Disease Detector
      </h1>

      <div className="w-full max-w-sm space-y-4 bg-white rounded-xl shadow-md p-4">
        <input
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          className="w-full text-sm"
        />

        <button
          onClick={handleUpload}
          disabled={isUploading}
          className="w-full bg-green-600 text-white py-3 rounded-xl text-lg font-semibold hover:bg-green-700 disabled:bg-gray-400 transition"
        >
          {isUploading ? "Analyzing..." : "Upload Leaf Image"}
        </button>

        {error && (
          <p className="text-red-600 text-sm text-center">{error}</p>
        )}

        {result && (
          <div className="border rounded-lg p-3 bg-green-50 text-sm">
            <p><strong>Disease:</strong> {result.disease}</p>
            <p><strong>Confidence:</strong> {result.confidence}</p>
            <p><strong>Severity:</strong> {result.severity}</p>
            <p><strong>Treatment:</strong> {result.treatment}</p>
          </div>
        )}
      </div>

      <p className="mt-6 text-gray-500 text-sm text-center">
        Simple AI detection for farmers
      </p>
    </div>
  );
}
