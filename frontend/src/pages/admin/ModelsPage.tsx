import React, { useState, useEffect } from 'react';
import { authAxios } from '../../services/authService';

interface Model {
  value: string;
  name: string;
}

const ModelsPage: React.FC = () => {
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = async () => {
    try {
      setLoading(true);
      const response = await authAxios.get('/api/models');
      setModels(response.data);
      
      // Set default selected model
      if (response.data.length > 0 && !selectedModel) {
        setSelectedModel(response.data[0].value);
      }
    } catch (err) {
      setError('Failed to fetch models. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedModel(e.target.value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedModel) {
      setError('Please select a model');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      // In a real application, you would update the default model in the database
      // For now, we'll just simulate the API call
      // await authAxios.post('/api/set-default-model', { model: selectedModel });
      
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setSuccess(`Model ${getModelName(selectedModel)} set as default successfully!`);
    } catch (err) {
      setError('Failed to update default model. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getModelName = (modelValue: string): string => {
    const model = models.find(m => m.value === modelValue);
    return model ? model.name : modelValue;
  };

  return (
    <div className="container mx-auto py-4">
      <div className="flex items-center mb-6">
        <div className="w-1.5 h-8 bg-gradient-to-b from-orange-500 to-orange-600 rounded-full mr-3"></div>
        <h1 className="text-2xl font-bold text-gray-800">Model Selection</h1>
      </div>
      
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 transition-all duration-300 hover:shadow-md">
        <div className="flex items-start mb-6">
          <div className="mr-4 p-3 bg-orange-50 rounded-lg">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-800">Select Default AI Model</h2>
        </div>
        
        {error && (
          <div className="mb-6 flex items-center p-4 border-l-4 border-red-500 bg-red-50 rounded-r-lg">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-red-500 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-red-800">{error}</span>
          </div>
        )}
        
        {success && (
          <div className="mb-6 flex items-center p-4 border-l-4 border-green-500 bg-green-50 rounded-r-lg">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-green-500 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-green-800">{success}</span>
          </div>
        )}
        
        {loading && !models.length ? (
          <div className="py-8 text-center">
            <div className="flex justify-center mb-3">
              <svg className="animate-spin h-8 w-8 text-orange-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
            <p className="text-gray-500">Loading available models...</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6 pl-[52px]">
            <div>
              <label htmlFor="model-select" className="block text-sm font-medium text-gray-700 mb-2">
                Choose the AI Model for Your Chatbot
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <select
                  id="model-select"
                  value={selectedModel}
                  onChange={handleModelChange}
                  className="block w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-orange-500 bg-white shadow-sm appearance-none"
                  disabled={loading}
                >
                  {models.map((model) => (
                    <option key={model.value} value={model.value}>
                      {model.name}
                    </option>
                  ))}
                </select>
                <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l4-4 4 4m0 6l-4 4-4-4" />
                  </svg>
                </div>
              </div>
              <p className="mt-1 text-sm text-gray-500 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Select the model that best fits your requirements and budget
              </p>
            </div>
            
            <div className="space-y-2">
              <h3 className="text-md font-medium text-gray-700">Model Information</h3>
              <div className="bg-gray-50 p-5 rounded-lg border border-gray-100">
                {selectedModel === 'llama-3.1-8b-instant' && (
                  <div className="flex">
                    <div className="mr-4 bg-blue-100 p-3 rounded-full h-fit">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-semibold text-gray-800">llama-3.1-8b-instant</p>
                      <p className="text-sm text-gray-600 mt-1 leading-relaxed">
                        A powerful open-source mixture-of-experts model with an extended context window of 32,768 tokens.
                        Great for handling complex reasoning tasks with long documents.
                      </p>
                    </div>
                  </div>
                )}
                {selectedModel === 'mistral' && (
                  <div className="flex">
                    <div className="mr-4 bg-purple-100 p-3 rounded-full h-fit">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-semibold text-gray-800">Mistral 7B</p>
                      <p className="text-sm text-gray-600 mt-1 leading-relaxed">
                        An efficient open-source model that offers a good balance of performance and speed.
                        Locally hosted using Ollama for faster response times.
                      </p>
                    </div>
                  </div>
                )}
                {selectedModel === 'gpt-4o' && (
                  <div className="flex">
                    <div className="mr-4 bg-green-100 p-3 rounded-full h-fit">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-semibold text-gray-800">GPT-4o</p>
                      <p className="text-sm text-gray-600 mt-1 leading-relaxed">
                        OpenAI's most capable model optimized for speed and conversational quality.
                        Excellent for complex reasoning and human-like responses, but requires API credit.
                      </p>
                    </div>
                  </div>
                )}
                {selectedModel === 'gpt-4o-mini' && (
                  <div className="flex">
                    <div className="mr-4 bg-teal-100 p-3 rounded-full h-fit">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-semibold text-gray-800">GPT-4o Mini</p>
                      <p className="text-sm text-gray-600 mt-1 leading-relaxed">
                        A smaller, faster version of GPT-4o that maintains high quality and costs less to run.
                        Good balance of performance and economy for most use cases.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
            
            <button
              type="submit"
              disabled={loading}
              className={`flex items-center px-4 py-2 rounded-lg shadow-sm transition-all duration-200 ${
                loading
                  ? 'bg-gray-300 cursor-not-allowed text-gray-500'
                  : 'bg-gradient-to-r from-orange-500 to-orange-600 text-white hover:from-orange-600 hover:to-orange-700 transform hover:translate-y-[-1px] hover:shadow active:translate-y-0'
              }`}
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Updating...
                </>
              ) : (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Set as Default Model
                </>
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default ModelsPage; 