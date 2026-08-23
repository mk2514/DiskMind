import { useState } from 'react';
import { sendChat } from '../api/client';
import type { ChatMessage } from '../types';

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');

  const handleSend = async () => {
    if (!input.trim()) return;
    const msg = input;
    setInput('');
    const newMessages = [...messages, { role: 'user' as const, content: msg }];
    setMessages(newMessages);
    
    try {
      const res = await sendChat(newMessages);
      setMessages(prev => [...prev, { role: 'assistant' as const, content: res.response }]);
    } catch (e) {
      console.error(e);
      setMessages(prev => [...prev, { role: 'assistant' as const, content: 'Error communicating with AI.' }]);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <h1 className="text-2xl font-bold text-black border-b border-surface-600 pb-2 mb-4">AI Copilot</h1>
      <div className="flex-1 overflow-y-auto p-6 bg-surface-800 border border-surface-600 mb-4 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`p-3 max-w-[80%] ${m.role === 'user' ? 'bg-black text-white ml-auto' : 'bg-surface-700 text-black border border-surface-600'}`}>
            {m.content}
          </div>
        ))}
        {messages.length === 0 && <p className="text-text-muted">Ask DiskMind a question about your storage!</p>}
      </div>
      <div className="flex gap-2">
        <input 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          className="flex-1 p-3 border border-surface-600 bg-surface-800 focus:outline-none focus:border-black"
          placeholder="Ask a question..."
        />
        <button onClick={handleSend} className="px-6 py-3 bg-black text-white font-bold hover:bg-gray-800">
          Send
        </button>
      </div>
    </div>
  );
}
