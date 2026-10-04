import React from 'react';

function renderInline(text, keyPrefix) {
  return text.split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*\n]+\*)/g).map((part, index) => {
    const key = `${keyPrefix}-${index}`;
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={key}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={key}>{part.slice(1, -1)}</code>;
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      return <em key={key}>{part.slice(1, -1)}</em>;
    }
    return part;
  });
}

function renderMessage(message) {
  const lines = message.split(/\r?\n/);
  const blocks = [];
  let paragraph = [];
  let list = [];
  let code = [];
  let inCodeBlock = false;

  const flushParagraph = () => {
    if (paragraph.length) {
      blocks.push(<p key={`p-${blocks.length}`}>{renderInline(paragraph.join(' '), `p-${blocks.length}`)}</p>);
      paragraph = [];
    }
  };
  const flushList = () => {
    if (list.length) {
      blocks.push(
        <ul key={`ul-${blocks.length}`}>
          {list.map((item, index) => <li key={`li-${index}`}>{renderInline(item, `li-${blocks.length}-${index}`)}</li>)}
        </ul>,
      );
      list = [];
    }
  };

  lines.forEach((line) => {
    if (line.trim().startsWith('```')) {
      flushParagraph();
      flushList();
      if (inCodeBlock) {
        blocks.push(<pre key={`pre-${blocks.length}`}><code>{code.join('\n')}</code></pre>);
        code = [];
      }
      inCodeBlock = !inCodeBlock;
      return;
    }

    if (inCodeBlock) {
      code.push(line);
      return;
    }

    const listItem = line.match(/^\s*[-*+]\s+(.+)$/);
    if (listItem) {
      flushParagraph();
      list.push(listItem[1]);
      return;
    }

    flushList();
    const heading = line.match(/^#{1,3}\s+(.+)$/);
    if (heading) {
      flushParagraph();
      blocks.push(<h3 key={`h-${blocks.length}`}>{renderInline(heading[1], `h-${blocks.length}`)}</h3>);
    } else if (line.trim()) {
      paragraph.push(line.trim());
    } else {
      flushParagraph();
    }
  });

  flushParagraph();
  flushList();
  if (inCodeBlock) {
    blocks.push(<pre key={`pre-${blocks.length}`}><code>{code.join('\n')}</code></pre>);
  }
  return blocks;
}

export default function ChatBubble({ message, isAi }) {
  return (
    <div className={`chat-bubble ${isAi ? 'chat-bubble-ai' : 'chat-bubble-user'}`}>
      {isAi ? renderMessage(message) : <p>{message}</p>}
    </div>
  );
}
