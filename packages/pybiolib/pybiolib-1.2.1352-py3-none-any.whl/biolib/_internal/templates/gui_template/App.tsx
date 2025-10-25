import { useState, useEffect } from "react";
import biolib from "./biolib-sdk";

export default function App() {
  const [outputFileData, setOutputFileData] = useState<Uint8Array | null>(null);
  const [loading, setLoading] = useState(true);

  const loadOutputData = async () => {
    setLoading(true);
    try {
      const data = await biolib.getOutputFileData("output.json");
      setOutputFileData(data);
    } catch (error) {
      console.error("Error loading output data:", error);
      setOutputFileData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOutputData();
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="text-center max-w-2xl mx-auto p-8">
        <h1 className="text-4xl font-bold mb-4">
          Hello, BioLib!
        </h1>
        <p className="text-lg mb-2">
          You have successfully set up your BioLib GUI application.
        </p>
        <p className="italic mb-6">
          This is a simple React template with Tailwind CSS styling.
        </p>

        <div className="mt-8 p-4 bg-white rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Example: Reading Output Files</h2>
          {loading ? (
            <p className="text-gray-500">Loading output.json...</p>
          ) : outputFileData ? (
            <div className="p-3 bg-gray-50 rounded text-left">
              <pre className="text-sm">{new TextDecoder().decode(outputFileData)}</pre>
            </div>
          ) : (
            <p className="text-red-500">Failed to load output.json</p>
          )}
        </div>
      </div>
    </div>
  );
}
