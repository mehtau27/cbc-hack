import React, { useState, useRef, useEffect } from 'react';
import { Upload, Mic, Square, Play, Pause, AlertCircle, CheckCircle, Download } from 'lucide-react';

export default function LectureEngagement() {
  const [audioFile, setAudioFile] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [transcript, setTranscript] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [userAnswers, setUserAnswers] = useState({});
  const [isGeneratingQuestions, setIsGeneratingQuestions] = useState(false);
  const [activeTab, setActiveTab] = useState('upload');
  const [audioURL, setAudioURL] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recognitionRef = useRef(null);
  const audioRef = useRef(null);

  const startTimeRef = useRef(null);

  useEffect(() => {
    // Check for speech recognition support
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      console.warn('Speech recognition not supported in this browser');
    }
  }, []);

  const startRecording = async () => {
    try {
      // Check for speech recognition support
      if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
        alert('Speech recognition is not supported in your browser. Please use Chrome or Edge for live transcription.');
        return;
      }

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Setup media recorder
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const url = URL.createObjectURL(audioBlob);
        setAudioURL(url);
        setAudioFile(audioBlob);
      };

      // Setup speech recognition
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';
      
      startTimeRef.current = Date.now();
      
      recognitionRef.current.onresult = (event) => {
        const results = event.results;
        
        for (let i = event.resultIndex; i < results.length; i++) {
          if (results[i].isFinal) {
            const elapsedMs = Date.now() - startTimeRef.current;
            const totalSeconds = Math.floor(elapsedMs / 1000);
            const hours = Math.floor(totalSeconds / 3600);
            const minutes = Math.floor((totalSeconds % 3600) / 60);
            const seconds = totalSeconds % 60;
            const timestamp = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            
            setTranscript(prev => [...prev, {
              timestamp,
              text: results[i][0].transcript,
              confidence: results[i][0].confidence
            }]);
          }
        }
      };
      
      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error !== 'no-speech' && event.error !== 'aborted') {
          alert(`Speech recognition error: ${event.error}. Make sure to speak clearly.`);
        }
      };
      
      recognitionRef.current.onend = () => {
        // Auto-restart if still recording
        if (isRecording && recognitionRef.current) {
          try {
            recognitionRef.current.start();
          } catch (e) {
            console.log('Recognition already started or stopped');
          }
        }
      };

      // Start both
      mediaRecorderRef.current.start();
      recognitionRef.current.start();
      
      setIsRecording(true);
      setTranscript([]);
      
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Error accessing microphone: ' + error.message + '\n\nPlease make sure you have granted microphone permissions.');
    }
  };

  const stopRecording = () => {
    setIsRecording(false);
    
    // Stop speech recognition
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
        recognitionRef.current.onend = null;
      } catch (e) {
        console.log('Recognition already stopped');
      }
    }
    
    // Stop media recorder
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file && (file.type.startsWith('audio/') || file.type.startsWith('video/'))) {
      setAudioFile(file);
      const url = URL.createObjectURL(file);
      setAudioURL(url);
      setTranscript([]);
      setQuestions([]);
    } else {
      alert('Please upload an audio or video file');
    }
  };

  const transcribeAudio = async () => {
    if (!audioFile) return;
    
    setIsTranscribing(true);
    setTranscript([]);
    
    try {
      // Option 1: Use AssemblyAI for real transcription (requires API key)
      // For hackathon demo, you can get a free API key at https://www.assemblyai.com/
      const USE_ASSEMBLYAI = false; // Set to true if you have an API key
      const ASSEMBLYAI_API_KEY = 'YOUR_API_KEY_HERE'; // Replace with your key
      
      if (USE_ASSEMBLYAI && ASSEMBLYAI_API_KEY !== 'YOUR_API_KEY_HERE') {
        // Upload file to AssemblyAI
        const uploadResponse = await fetch('https://api.assemblyai.com/v2/upload', {
          method: 'POST',
          headers: {
            'authorization': ASSEMBLYAI_API_KEY,
          },
          body: audioFile
        });
        
        const { upload_url } = await uploadResponse.json();
        
        // Request transcription
        const transcriptResponse = await fetch('https://api.assemblyai.com/v2/transcript', {
          method: 'POST',
          headers: {
            'authorization': ASSEMBLYAI_API_KEY,
            'content-type': 'application/json'
          },
          body: JSON.stringify({
            audio_url: upload_url,
            speaker_labels: false
          })
        });
        
        const { id } = await transcriptResponse.json();
        
        // Poll for completion
        let transcriptData;
        while (true) {
          const pollingResponse = await fetch(`https://api.assemblyai.com/v2/transcript/${id}`, {
            headers: {
              'authorization': ASSEMBLYAI_API_KEY,
            }
          });
          
          transcriptData = await pollingResponse.json();
          
          if (transcriptData.status === 'completed') {
            break;
          } else if (transcriptData.status === 'error') {
            throw new Error('Transcription failed');
          }
          
          await new Promise(resolve => setTimeout(resolve, 3000));
        }
        
        // Convert to our format with timestamps
        const words = transcriptData.words || [];
        const segments = [];
        let currentSegment = { text: '', start: 0 };
        
        words.forEach((word, index) => {
          currentSegment.text += word.text + ' ';
          
          // Create new segment every 10 seconds or 50 words
          if (index % 50 === 49 || index === words.length - 1) {
            const milliseconds = currentSegment.start;
            const totalSeconds = Math.floor(milliseconds / 1000);
            const hours = Math.floor(totalSeconds / 3600);
            const minutes = Math.floor((totalSeconds % 3600) / 60);
            const seconds = totalSeconds % 60;
            const timestamp = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            
            segments.push({
              timestamp,
              text: currentSegment.text.trim()
            });
            
            if (index < words.length - 1) {
              currentSegment = { text: '', start: words[index + 1].start };
            }
          }
        });
        
        setTranscript(segments);
        setIsTranscribing(false);
        return;
      }
      
      // Option 2: Fallback - Manual transcription mode
      alert('For accurate transcription of uploaded files, you have two options:\n\n1. Get a free AssemblyAI API key and add it to the code\n2. Use the "Record Live" tab to transcribe in real-time as you play the video\n\nFor now, creating a sample transcript so you can test the question generation feature.');
      
      // Create a sample transcript for demo purposes
      const sampleTranscript = [
        { timestamp: '00:00:00', text: 'This is a sample transcript. To get real transcription, please use one of these methods: 1) Add an AssemblyAI API key to the code, or 2) Use the Record Live feature while playing your video.' },
        { timestamp: '00:00:15', text: 'You can still test the question generation feature with this sample text. The AI will generate questions based on whatever transcript is provided.' }
      ];
      
      setTranscript(sampleTranscript);
      setIsTranscribing(false);
      
    } catch (error) {
      console.error('Transcription error:', error);
      alert('Error during transcription: ' + error.message);
      setIsTranscribing(false);
    }
  };

  const generateQuestions = async () => {
    if (transcript.length === 0) return;
    
    setIsGeneratingQuestions(true);
    
    const fullTranscript = transcript.map(t => `[${t.timestamp}] ${t.text}`).join('\n');
    
    try {
      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 2000,
          messages: [
            {
              role: 'user',
              content: `Based on this lecture transcript with timestamps, generate 5 engaging multiple-choice questions to test student comprehension and engagement. 

Transcript:
${fullTranscript}

CRITICAL: Respond ONLY with valid JSON in this EXACT format. DO NOT include any text outside the JSON structure, including backticks or markdown formatting:

{
  "questions": [
    {
      "question": "Question text here",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correctAnswer": 0,
      "explanation": "Why this answer is correct",
      "timestamp": "00:00:00"
    }
  ]
}

The questions should:
1. Test understanding of key concepts
2. Reference specific timestamps from the lecture
3. Have 4 options each
4. Include explanations
5. Range from basic recall to application questions`
            }
          ]
        })
      });

      const data = await response.json();
      let responseText = data.content[0].text;
      
      // Strip markdown formatting if present
      responseText = responseText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
      
      const parsedData = JSON.parse(responseText);
      setQuestions(parsedData.questions);
      setIsGeneratingQuestions(false);
    } catch (error) {
      console.error('Error generating questions:', error);
      alert('Error generating questions. Please try again.');
      setIsGeneratingQuestions(false);
    }
  };

  const handleAnswerSelect = (questionIndex, optionIndex) => {
    setUserAnswers({
      ...userAnswers,
      [questionIndex]: optionIndex
    });
  };

  const downloadTranscript = () => {
    const text = transcript.map(t => `[${t.timestamp}] ${t.text}`).join('\n\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'lecture-transcript.txt';
    a.click();
  };

  const toggleAudio = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-xl shadow-lg p-8 mb-6">
          <h1 className="text-4xl font-bold text-indigo-900 mb-2">Lecture Engagement System</h1>
          <p className="text-gray-600 mb-6">Transcribe lectures and generate questions to ensure student engagement</p>
          
          {/* Tab Navigation */}
          <div className="flex gap-4 mb-6 border-b">
            <button
              onClick={() => setActiveTab('upload')}
              className={`pb-3 px-4 font-medium transition-colors ${
                activeTab === 'upload'
                  ? 'border-b-2 border-indigo-600 text-indigo-600'
                  : 'text-gray-500 hover:text-indigo-600'
              }`}
            >
              <Upload className="inline-block w-4 h-4 mr-2" />
              Upload Audio
            </button>
            <button
              onClick={() => setActiveTab('record')}
              className={`pb-3 px-4 font-medium transition-colors ${
                activeTab === 'record'
                  ? 'border-b-2 border-indigo-600 text-indigo-600'
                  : 'text-gray-500 hover:text-indigo-600'
              }`}
            >
              <Mic className="inline-block w-4 h-4 mr-2" />
              Record Live
            </button>
          </div>

          {/* Upload Tab */}
          {activeTab === 'upload' && (
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <p className="text-blue-800 flex items-center text-sm">
                  <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0" />
                  <span><strong>Transcription Note:</strong> For accurate transcription of uploaded files, get a free AssemblyAI API key at assemblyai.com and add it to the code (line 185). Alternatively, use "Record Live" while playing your video for real-time transcription.</span>
                </p>
              </div>

              <div className="border-2 border-dashed border-indigo-300 rounded-lg p-8 text-center hover:border-indigo-500 transition-colors">
                <input
                  type="file"
                  accept="audio/*,video/*"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="audio-upload"
                />
                <label htmlFor="audio-upload" className="cursor-pointer">
                  <Upload className="w-12 h-12 mx-auto text-indigo-600 mb-3" />
                  <p className="text-lg font-medium text-gray-700">Upload Lecture Audio or Video</p>
                  <p className="text-sm text-gray-500 mt-1">MP3, WAV, MP4, MOV, or other audio/video formats</p>
                </label>
              </div>

              {audioFile && !isRecording && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <p className="text-green-800 font-medium flex items-center">
                    <CheckCircle className="w-5 h-5 mr-2" />
                    {audioFile.type.startsWith('video/') ? 'Video' : 'Audio'} file loaded: {audioFile.name || 'Recorded audio'}
                  </p>
                  {audioURL && (
                    <div className="mt-3 flex items-center gap-3">
                      {audioFile.type.startsWith('video/') ? (
                        <video 
                          ref={audioRef} 
                          src={audioURL} 
                          controls 
                          className="w-full max-w-2xl rounded-lg"
                          onEnded={() => setIsPlaying(false)}
                        />
                      ) : (
                        <>
                          <button
                            onClick={toggleAudio}
                            className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2"
                          >
                            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                            {isPlaying ? 'Pause' : 'Play'} Audio
                          </button>
                          <audio ref={audioRef} src={audioURL} onEnded={() => setIsPlaying(false)} />
                        </>
                      )}
                    </div>
                  )}
                </div>
              )}

              {audioFile && (
                <button
                  onClick={transcribeAudio}
                  disabled={isTranscribing}
                  className="w-full bg-indigo-600 text-white py-3 rounded-lg font-medium hover:bg-indigo-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {isTranscribing ? 'Transcribing...' : 'Transcribe Audio'}
                </button>
              )}
            </div>
          )}

          {/* Record Tab */}
          {activeTab === 'record' && (
            <div className="space-y-4">
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
                <p className="text-amber-800 flex items-center">
                  <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0" />
                  <span className="text-sm">Live recording uses your browser's speech recognition. For best results, speak clearly and ensure minimal background noise.</span>
                </p>
              </div>

              <div className="text-center py-8">
                {!isRecording ? (
                  <button
                    onClick={startRecording}
                    className="bg-red-600 text-white px-8 py-4 rounded-full font-medium hover:bg-red-700 transition-colors flex items-center gap-3 mx-auto text-lg"
                  >
                    <Mic className="w-6 h-6" />
                    Start Recording Lecture
                  </button>
                ) : (
                  <button
                    onClick={stopRecording}
                    className="bg-gray-800 text-white px-8 py-4 rounded-full font-medium hover:bg-gray-900 transition-colors flex items-center gap-3 mx-auto text-lg animate-pulse"
                  >
                    <Square className="w-6 h-6" />
                    Stop Recording
                  </button>
                )}
              </div>

              {isRecording && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                  <div className="flex items-center justify-center gap-2 text-red-800 font-medium">
                    <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse"></div>
                    Recording in progress...
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Transcript Section */}
        {transcript.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-8 mb-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-indigo-900">Lecture Transcript</h2>
              <button
                onClick={downloadTranscript}
                className="bg-indigo-100 text-indigo-700 px-4 py-2 rounded-lg hover:bg-indigo-200 transition-colors flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Download
              </button>
            </div>
            <div className="space-y-3 max-h-96 overflow-y-auto bg-gray-50 rounded-lg p-4">
              {transcript.map((item, index) => (
                <div key={index} className="border-l-4 border-indigo-500 pl-4 py-2">
                  <span className="text-indigo-600 font-mono text-sm font-medium">[{item.timestamp}]</span>
                  <p className="text-gray-800 mt-1">{item.text}</p>
                </div>
              ))}
            </div>

            <button
              onClick={generateQuestions}
              disabled={isGeneratingQuestions}
              className="w-full mt-4 bg-green-600 text-white py-3 rounded-lg font-medium hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {isGeneratingQuestions ? 'Generating Questions...' : 'Generate Engagement Questions'}
            </button>
          </div>
        )}

        {/* Questions Section */}
        {questions.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold text-indigo-900 mb-6">Engagement Questions</h2>
            <div className="space-y-6">
              {questions.map((q, qIndex) => (
                <div key={qIndex} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-lg font-semibold text-gray-800 flex-1">
                      {qIndex + 1}. {q.question}
                    </h3>
                    <span className="text-indigo-600 font-mono text-sm bg-indigo-50 px-3 py-1 rounded ml-4">
                      {q.timestamp}
                    </span>
                  </div>

                  <div className="space-y-2">
                    {q.options.map((option, oIndex) => {
                      const isSelected = userAnswers[qIndex] === oIndex;
                      const isCorrect = q.correctAnswer === oIndex;
                      const showResult = userAnswers[qIndex] !== undefined;

                      return (
                        <button
                          key={oIndex}
                          onClick={() => handleAnswerSelect(qIndex, oIndex)}
                          className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                            !showResult
                              ? isSelected
                                ? 'border-indigo-500 bg-indigo-50'
                                : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
                              : isCorrect
                              ? 'border-green-500 bg-green-50'
                              : isSelected
                              ? 'border-red-500 bg-red-50'
                              : 'border-gray-200 bg-gray-50 opacity-60'
                          }`}
                        >
                          <div className="flex items-center">
                            <span className="font-medium mr-3 text-gray-600">
                              {String.fromCharCode(65 + oIndex)}.
                            </span>
                            <span className={showResult && isCorrect ? 'font-medium text-green-700' : ''}>
                              {option}
                            </span>
                            {showResult && isCorrect && (
                              <CheckCircle className="w-5 h-5 ml-auto text-green-600" />
                            )}
                          </div>
                        </button>
                      );
                    })}
                  </div>

                  {userAnswers[qIndex] !== undefined && (
                    <div className={`mt-4 p-4 rounded-lg ${
                      userAnswers[qIndex] === q.correctAnswer
                        ? 'bg-green-50 border border-green-200'
                        : 'bg-amber-50 border border-amber-200'
                    }`}>
                      <p className={`font-medium mb-2 ${
                        userAnswers[qIndex] === q.correctAnswer ? 'text-green-800' : 'text-amber-800'
                      }`}>
                        {userAnswers[qIndex] === q.correctAnswer ? '✓ Correct!' : '✗ Incorrect'}
                      </p>
                      <p className="text-gray-700">{q.explanation}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Score Summary */}
            {Object.keys(userAnswers).length === questions.length && (
              <div className="mt-8 bg-indigo-50 border-2 border-indigo-200 rounded-lg p-6 text-center">
                <h3 className="text-2xl font-bold text-indigo-900 mb-2">
                  Your Score: {questions.filter((q, i) => userAnswers[i] === q.correctAnswer).length} / {questions.length}
                </h3>
                <p className="text-indigo-700">
                  {(questions.filter((q, i) => userAnswers[i] === q.correctAnswer).length / questions.length * 100).toFixed(0)}% Correct
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
