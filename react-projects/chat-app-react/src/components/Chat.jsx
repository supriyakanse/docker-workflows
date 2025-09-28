import { useState, useEffect, useRef } from 'react';
import { sendMessage, fetchEmails, buildVectorstore } from '../services/chatService';

export default function Chat() {
  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [initProgress, setInitProgress] = useState(0);
  const [initStage, setInitStage] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    const init = async () => {
      try {
        const initialized = sessionStorage.getItem('chatInitialized');
        if (!initialized) {
          setInitStage('Fetching emails...');
          setInitProgress(20);
          await fetchEmails();
          
          setInitStage('Building knowledge base...');
          setInitProgress(60);
          await buildVectorstore();
          
          setInitStage('Finalizing setup...');
          setInitProgress(90);
          await new Promise(resolve => setTimeout(resolve, 500));
          
          setInitProgress(100);
          setInitStage('Ready!');
          await new Promise(resolve => setTimeout(resolve, 300));
          
          sessionStorage.setItem('chatInitialized', 'true');
        }
      } catch (err) {
        console.error('Initialization error:', err);
        setInitStage('Error occurred');
      } finally {
        setLoading(false);
      }
    };

    init();
  }, []);

  const handleSend = async () => {
    if (!inputText.trim() || sending) return;

    const userMessage = inputText;
    setInputText('');
    setMessages(prev => [...prev, { role: 'user', text: userMessage, id: Date.now() }]);
    setSending(true);

    try {
      const res = await sendMessage(userMessage);
      setMessages(prev => [...prev, { role: 'bot', text: res.data.answer, id: Date.now() + 1 }]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { role: 'bot', text: 'Error sending message', id: Date.now() + 1 }]);
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-content">
          <div className="logo-container">
            <div className="logo-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 8L10.89 13.26C11.2187 13.4793 11.6049 13.5963 12 13.5963C12.3951 13.5963 12.7813 13.4793 13.11 13.26L21 8M5 19H19C19.5304 19 20.0391 18.7893 20.4142 18.4142C20.7893 18.0391 21 17.5304 21 17V7C21 6.46957 20.7893 5.96086 20.4142 5.58579C20.0391 5.21071 19.5304 5 19 5H5C4.46957 5 3.96086 5.21071 3.58579 5.58579C3.21071 5.96086 3 6.46957 3 7V17C3 17.5304 3.21071 18.0391 3.58579 18.4142C3.96086 18.7893 4.46957 19 5 19Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <h1 className="logo-text">MailMentor</h1>
          </div>
          
          <div className="progress-container">
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${initProgress}%` }}
              />
            </div>
            <p className="progress-text">{initStage}</p>
          </div>
          
          <div className="loading-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
        
        <div className="background-animation">
          <div className="floating-bubble bubble-1"></div>
          <div className="floating-bubble bubble-2"></div>
          <div className="floating-bubble bubble-3"></div>
          <div className="floating-bubble bubble-4"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-app">
      <div className="chat-header">
        <div className="header-content">
          <div className="header-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 8L10.89 13.26C11.2187 13.4793 11.6049 13.5963 12 13.5963C12.3951 13.5963 12.7813 13.4793 13.11 13.26L21 8M5 19H19C19.5304 19 20.0391 18.7893 20.4142 18.4142C20.7893 18.0391 21 17.5304 21 17V7C21 6.46957 20.7893 5.96086 20.4142 5.58579C20.0391 5.21071 19.5304 5 19 5H5C4.46957 5 3.96086 5.21071 3.58579 5.58579C3.21071 5.96086 3 6.46957 3 7V17C3 17.5304 3.21071 18.0391 3.58579 18.4142C3.96086 18.7893 4.46957 19 5 19Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h1 className="header-title">MailMentor</h1>
          <div className="status-indicator">
            <div className="status-dot"></div>
            <span>Online</span>
          </div>
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <div className="welcome-icon">👋</div>
            <h2>Welcome to MailMentor!</h2>
            <p>I'm here to help you with your emails. Ask me anything!</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={msg.id}
              className={`message ${msg.role === 'user' ? 'user-message' : 'bot-message'}`}
              style={{ animationDelay: `${idx * 0.1}s` }}
            >
              <div className="message-content">
                {msg.role === 'bot' && (
                  <div className="bot-avatar">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 2C13.1046 2 14 2.89543 14 4C14 5.10457 13.1046 6 12 6C10.8954 6 10 5.10457 10 4C10 2.89543 10.8954 2 12 2Z" fill="currentColor"/>
                      <path d="M21 9V7C21 5.89543 20.1046 5 19 5H5C3.89543 5 3 5.89543 3 7V9M21 9C21 10.1046 20.1046 11 19 11H5C3.89543 11 3 10.1046 3 9M21 9V17C21 18.1046 20.1046 19 19 19H5C3.89543 19 3 18.1046 3 17V9" stroke="currentColor" strokeWidth="2"/>
                    </svg>
                  </div>
                )}
                <div className="message-bubble">
                  {msg.text}
                </div>
              </div>
            </div>
          ))
        )}
        
        {sending && (
          <div className="message bot-message typing-indicator">
            <div className="message-content">
              <div className="bot-avatar">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2C13.1046 2 14 2.89543 14 4C14 5.10457 13.1046 6 12 6C10.8954 6 10 5.10457 10 4C10 2.89543 10.8954 2 12 2Z" fill="currentColor"/>
                  <path d="M21 9V7C21 5.89543 20.1046 5 19 5H5C3.89543 5 3 5.89543 3 7V9M21 9C21 10.1046 20.1046 11 19 11H5C3.89543 11 3 10.1046 3 9M21 9V17C21 18.1046 20.1046 19 19 19H5C3.89543 19 3 18.1046 3 17V9" stroke="currentColor" strokeWidth="2"/>
                </svg>
              </div>
              <div className="typing-animation">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-section">
        <div className="input-container">
          <input
            type="text"
            value={inputText}
            onChange={e => setInputText(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder={sending ? "MailMentor is typing..." : "Type your message..."}
            disabled={sending}
            className="message-input"
          />
          <button
            onClick={handleSend}
            disabled={sending || !inputText.trim()}
            className="send-button"
          >
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      </div>

      <style jsx>{`
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }

        /* Loading Screen */
        .loading-screen {
          position: fixed;
          top: 0;
          left: 0;
          width: 100vw;
          height: 100vh;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 1000;
          overflow: hidden;
        }

        .loading-content {
          text-align: center;
          color: white;
          z-index: 2;
          animation: fadeInUp 0.8s ease-out;
        }

        .logo-container {
          margin-bottom: 3rem;
        }

        .logo-icon {
          width: 80px;
          height: 80px;
          margin: 0 auto 1rem;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          backdrop-filter: blur(10px);
          animation: float 3s ease-in-out infinite;
        }

        .logo-icon svg {
          width: 40px;
          height: 40px;
          color: white;
        }

        .logo-text {
          font-size: 2.5rem;
          font-weight: 700;
          margin-bottom: 0.5rem;
          background: linear-gradient(45deg, #fff, #e0e7ff);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .progress-container {
          margin: 2rem 0;
          width: 300px;
        }

        .progress-bar {
          width: 100%;
          height: 6px;
          background: rgba(255, 255, 255, 0.2);
          border-radius: 10px;
          overflow: hidden;
          margin-bottom: 1rem;
        }

        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #4facfe, #00f2fe);
          border-radius: 10px;
          transition: width 0.5s ease;
          box-shadow: 0 0 20px rgba(79, 172, 254, 0.5);
        }

        .progress-text {
          font-size: 1rem;
          opacity: 0.9;
          margin-bottom: 1rem;
        }

        .loading-dots {
          display: flex;
          justify-content: center;
          gap: 8px;
        }

        .loading-dots span {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.8);
          animation: bounce 1.4s ease-in-out infinite both;
        }

        .loading-dots span:nth-child(1) { animation-delay: -0.32s; }
        .loading-dots span:nth-child(2) { animation-delay: -0.16s; }

        .background-animation {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          overflow: hidden;
        }

        .floating-bubble {
          position: absolute;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(5px);
          animation: floatBubble 20s infinite linear;
        }

        .bubble-1 { width: 80px; height: 80px; left: 10%; animation-delay: 0s; }
        .bubble-2 { width: 120px; height: 120px; left: 70%; animation-delay: -5s; }
        .bubble-3 { width: 60px; height: 60px; left: 40%; animation-delay: -10s; }
        .bubble-4 { width: 100px; height: 100px; left: 80%; animation-delay: -15s; }

        /* Main Chat App */
        .chat-app {
          display: flex;
          flex-direction: column;
          height: 100vh;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
          background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
          animation: slideIn 0.6s ease-out;
        }

        /* Header */
        .chat-header {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          border-bottom: 1px solid rgba(0, 0, 0, 0.1);
          padding: 1rem 2rem;
          position: sticky;
          top: 0;
          z-index: 100;
          animation: slideDown 0.8s ease-out;
        }

        .header-content {
          display: flex;
          align-items: center;
          justify-content: space-between;
          max-width: 900px;
          margin: 0 auto;
        }

        .header-icon {
          width: 40px;
          height: 40px;
          background: linear-gradient(135deg, #667eea, #764ba2);
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          margin-right: 1rem;
        }

        .header-icon svg {
          width: 20px;
          height: 20px;
        }

        .header-title {
          font-size: 1.5rem;
          font-weight: 700;
          color: #2d3748;
          flex: 1;
        }

        .status-indicator {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: #4a5568;
          font-size: 0.875rem;
        }

        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #48bb78;
          animation: pulse 2s infinite;
        }

        /* Messages Area */
        .chat-messages {
          flex: 1;
          overflow-y: auto;
          padding: 2rem;
          display: flex;
          flex-direction: column;
          gap: 1rem;
          max-width: 900px;
          margin: 0 auto;
          width: 100%;
        }

        .welcome-message {
          text-align: center;
          padding: 4rem 2rem;
          color: #4a5568;
          animation: fadeInUp 1s ease-out;
        }

        .welcome-icon {
          font-size: 4rem;
          margin-bottom: 1rem;
        }

        .welcome-message h2 {
          font-size: 2rem;
          margin-bottom: 1rem;
          color: #2d3748;
        }

        .welcome-message p {
          font-size: 1.125rem;
          opacity: 0.8;
        }

        .message {
          display: flex;
          margin-bottom: 1rem;
          animation: messageSlideIn 0.5s ease-out forwards;
          opacity: 0;
          transform: translateY(20px);
        }

        .user-message {
          justify-content: flex-end;
        }

        .bot-message {
          justify-content: flex-start;
        }

        .message-content {
          display: flex;
          align-items: flex-end;
          gap: 0.75rem;
          max-width: 70%;
        }

        .user-message .message-content {
          flex-direction: row-reverse;
        }

        .bot-avatar {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background: linear-gradient(135deg, #667eea, #764ba2);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          flex-shrink: 0;
        }

        .bot-avatar svg {
          width: 18px;
          height: 18px;
        }

        .message-bubble {
          padding: 0.75rem 1rem;
          border-radius: 1.25rem;
          font-size: 0.95rem;
          line-height: 1.5;
          word-wrap: break-word;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .user-message .message-bubble {
          background: linear-gradient(135deg, #667eea, #764ba2);
          color: white;
          border-bottom-right-radius: 0.5rem;
        }

        .bot-message .message-bubble {
          background: white;
          color: #2d3748;
          border-bottom-left-radius: 0.5rem;
          border: 1px solid rgba(0, 0, 0, 0.05);
        }

        .typing-indicator .typing-animation {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 1rem;
          background: white;
          border-radius: 1.25rem;
          border-bottom-left-radius: 0.5rem;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .typing-animation span {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #cbd5e0;
          animation: typingBounce 1.4s ease-in-out infinite both;
        }

        .typing-animation span:nth-child(1) { animation-delay: -0.32s; }
        .typing-animation span:nth-child(2) { animation-delay: -0.16s; }

        /* Input Section */
        .chat-input-section {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          border-top: 1px solid rgba(0, 0, 0, 0.1);
          padding: 1.5rem 2rem;
          position: sticky;
          bottom: 0;
          animation: slideUp 0.8s ease-out;
        }

        .input-container {
          display: flex;
          gap: 1rem;
          max-width: 900px;
          margin: 0 auto;
          align-items: flex-end;
        }

        .message-input {
          flex: 1;
          padding: 0.875rem 1.25rem;
          border: 2px solid #e2e8f0;
          border-radius: 1.5rem;
          font-size: 1rem;
          outline: none;
          background: white;
          transition: all 0.2s ease;
          resize: none;
          min-height: 44px;
          max-height: 120px;
          color: #2d3748;
        }

        .message-input:focus {
          border-color: #667eea;
          box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .message-input:disabled {
          background: #f7fafc;
          color: #a0aec0;
          cursor: not-allowed;
        }

        .send-button {
          width: 48px;
          height: 48px;
          border: none;
          border-radius: 50%;
          background: linear-gradient(135deg, #667eea, #764ba2);
          color: white;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s ease;
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
          flex-shrink: 0;
        }

        .send-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
        }

        .send-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
          transform: none;
          box-shadow: 0 2px 6px rgba(102, 126, 234, 0.2);
        }

        .send-button svg {
          width: 20px;
          height: 20px;
        }

        /* Animations */
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(40px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes slideIn {
          from {
            opacity: 0;
            transform: scale(0.95);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes messageSlideIn {
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes bounce {
          0%, 80%, 100% {
            transform: scale(0);
          }
          40% {
            transform: scale(1);
          }
        }

        @keyframes typingBounce {
          0%, 80%, 100% {
            transform: scale(0.8);
            opacity: 0.6;
          }
          40% {
            transform: scale(1);
            opacity: 1;
          }
        }

        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }

        @keyframes floatBubble {
          from {
            transform: translateY(100vh) rotate(0deg);
            opacity: 0;
          }
          10% {
            opacity: 1;
          }
          90% {
            opacity: 1;
          }
          to {
            transform: translateY(-100px) rotate(360deg);
            opacity: 0;
          }
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        /* Responsive Design */
        @media (max-width: 768px) {
          .chat-header {
            padding: 1rem;
          }

          .header-title {
            font-size: 1.25rem;
          }

          .chat-messages {
            padding: 1rem;
          }

          .message-content {
            max-width: 85%;
          }

          .chat-input-section {
            padding: 1rem;
          }

          .welcome-message {
            padding: 2rem 1rem;
          }

          .welcome-message h2 {
            font-size: 1.5rem;
          }

          .logo-text {
            font-size: 2rem;
          }

          .progress-container {
            width: 250px;
          }
        }

        @media (max-width: 480px) {
          .header-content {
            flex-wrap: wrap;
            gap: 0.5rem;
          }

          .status-indicator {
            font-size: 0.75rem;
          }

          .message-content {
            max-width: 95%;
          }

          .input-container {
            gap: 0.5rem;
          }

          .send-button {
            width: 44px;
            height: 44px;
          }

          .logo-text {
            font-size: 1.75rem;
          }

          .progress-container {
            width: 200px;
          }
        }

        /* Custom scrollbar */
        .chat-messages::-webkit-scrollbar {
          width: 6px;
        }

        .chat-messages::-webkit-scrollbar-track {
          background: transparent;
        }

        .chat-messages::-webkit-scrollbar-thumb {
          background: rgba(0, 0, 0, 0.2);
          border-radius: 3px;
        }

        .chat-messages::-webkit-scrollbar-thumb:hover {
          background: rgba(0, 0, 0, 0.3);
        }
      `}</style>
    </div>
  );
}