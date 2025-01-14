import React, { useState } from 'react';

function App() {
  const [fRS3Output, setFRS3Output] = useState('');
  const [fRS3loading, setFRS3Loading] = useState(false);
  const [fRS3error, setFRS3Error] = useState('');
  const [analysisOutput, setAnalysisOutput] = useState('');
  const [analysisError, setAnalysisError] = useState('');
  const [analysisLoading, setanalysisLoading] = useState(false);

  const callDocumentIngestionFunction = async () => {
    setFRS3Loading(true);
    setFRS3Error('');
    try {
      // Replace this URL with your actual Lambda function URL
      // const lambdaUrl = "https://zmv8ad1dmk.execute-api.us-west-2.amazonaws.com/newstage";
      const fetchReadS3lambdaUrl = "https://m4gqxf0odb.execute-api.us-west-2.amazonaws.com/prod/api/llm/content/canvas"

      const response = await fetch(fetchReadS3lambdaUrl, {
        method: 'GET', // Change this method if your Lambda expects a POST request
      });

      if (response.ok) {
        const result = await response.text();
        setFRS3Output(result);
      } else {
        setFRS3Error('Failed to fetch data from Lambda');
      }
    } catch (err) {
      setFRS3Error('Error calling Lambda function');
      console.error(err);
    } finally {
      setFRS3Loading(false);
    }
  };

  const callRecentCourseDataAnalysis = async () => {
    setanalysisLoading(true);
    setAnalysisError('');
    try {
      // Replace this URL with your actual Lambda function URL
      const recentCourseDataAnalysisUrl = "https://m4gqxf0odb.execute-api.us-west-2.amazonaws.com/prod/api/llm/analysis/data";
      const courseId = "course-id-123"; // Replace with actual course ID
      const period = "WEEK"; // Replace with actual period, e.g., WEEK, MONTH, or TERM

      const response = await fetch(`${recentCourseDataAnalysisUrl}?course=${courseId}&period=${period}`, {
        method: 'GET',
      });

      if (response.ok) {
        const result = await response.json(); // Assume response is JSON
        setAnalysisOutput(JSON.stringify(result, null, 2)); // Pretty print JSON output
      } else {
        setAnalysisError('Failed to fetch data from Lambda');
      }
    } catch (err) {
      setAnalysisError('Error calling Lambda function');
      console.error(err);
    } finally {
      setanalysisLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Lambda Text Extraction api</h1>
      <button onClick={callDocumentIngestionFunction} disabled={fRS3loading}>
        {fRS3loading ? 'Loading...' : 'Call Lambda'}
      </button>
      {fRS3error && <p style={{ color: 'red' }}>{fRS3error}</p>}
      <h3>Output:</h3>
      <pre>{fRS3Output}</pre>

      <button onClick={callRecentCourseDataAnalysis} disabled={analysisLoading}>
        {analysisLoading ? 'Loading...' : 'Call Recent Course Data Analysis Lambda'}
      </button>
      {analysisError && <p style={{ color: 'red' }}>{analysisError}</p>}
      <h3>Output for Recent Course Data Analysis:</h3>
      <pre>{analysisOutput}</pre>

    </div>
  );
}

export default App;