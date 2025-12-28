# University Chatbot Design Guidelines

## Design Approach
**Reference-Based with System Foundation**: Draw inspiration from modern chat applications (ChatGPT, Discord) combined with educational platform aesthetics (Notion, Linear) for a clean, trustworthy interface. Prioritize clarity and accessibility for Korean university students.

## Typography

**Font Family:**
- Primary: 'Noto Sans KR' (Google Fonts) - Excellent Korean/English rendering
- Fallback: -apple-system, system-ui

**Type Scale:**
- Hero/Welcome: text-3xl to text-4xl, font-semibold
- Section Headers: text-xl, font-semibold
- Chat Messages: text-base (16px), font-normal
- Category Tags: text-sm, font-medium
- Timestamps/Metadata: text-xs, text-gray-500

## Layout System

**Spacing Primitives:** Use Tailwind units of 2, 3, 4, 6, 8, 12 for consistency
- Component padding: p-4 to p-6
- Section spacing: py-8 to py-12
- Message bubbles: p-3 to p-4
- Button padding: px-4 py-2

**Container Structure:**
- Max width: max-w-4xl for chat area (optimal readability)
- Full width: Categories and header
- Mobile: Full viewport width with px-4 padding

## Core Components

### 1. Header
- Fixed top navigation
- Logo/university branding (left)
- Optional settings/menu (right)
- Subtle bottom border
- Height: h-16
- Padding: px-4 md:px-8

### 2. Category Navigation Bar
- Horizontal scrollable pill buttons
- Sticky positioning below header (top-16)
- Pills: Rounded-full, px-4 py-2
- Gap between pills: gap-2
- Hash prefix (#) for each category
- Active state: Distinct visual treatment

### 3. Chat Interface

**Message Bubbles:**
- User messages: Right-aligned, max-w-2xl
- AI responses: Left-aligned, max-w-3xl
- Padding: p-4
- Rounded corners: rounded-2xl
- Shadow: shadow-sm
- Spacing between messages: space-y-4

**Message Structure:**
- Avatar/icon for AI (left, 8x8 or 10x10)
- Timestamp below message: text-xs
- Source links as inline buttons within AI messages

### 4. Input Area
- Fixed bottom positioning
- Container: px-4 pb-4 md:px-8 md:pb-6
- Input wrapper: max-w-4xl mx-auto
- Text input: Rounded-full, pl-6 pr-12, py-3
- Send button: Absolute right positioning, rounded-full, p-2
- Shadow: shadow-lg for lift effect

### 5. Quick Suggestions
Display when:
- Initial load (recommended questions)
- After category selection
- Error states (alternative suggestions)

Format:
- Chip/pill style: rounded-full, px-4 py-2
- Flex wrap layout: flex-wrap gap-2
- Appear below input or within conversation flow

### 6. Source Citations
- Inline link buttons: text-sm, underline decoration
- External link icon
- Hover state: Slight opacity change
- Format: "▸ [Document Title] →"

### 7. Error/Empty States
- Centered content: text-center
- Icon (optional): mb-4
- Message: text-base, mb-4
- Suggestion categories below: Same pill format as navigation

## Images

**Logo/Branding:**
- University logo in header (height: h-8 to h-10)
- Optional: Small chatbot mascot/icon for AI avatar

**No hero image needed** - This is a chat application where the conversation interface is immediately visible.

**Icons:**
- Use Heroicons via CDN
- Send icon, settings, external link indicators
- AI avatar icon (chat bubble or sparkle)

## Layout Specifications

**Main Chat View:**
```
[Fixed Header - 16 units height]
[Sticky Category Bar - auto height]
[Chat Messages Container - flex-1, overflow-y-auto]
  - Initial welcome message
  - Conversation history
  - Messages scroll from bottom
[Fixed Input Area - bottom]
```

**Mobile Adaptations:**
- Stack categories vertically on very small screens
- Reduce message bubble max-width
- Adjust padding: p-3 instead of p-4
- Single column throughout

## Interaction Patterns

**Conversation Flow:**
1. User types or selects category
2. Quick suggestions appear (if category)
3. User clicks suggestion or enters custom question
4. AI response streams in (if implementing streaming)
5. Source links appear at end of response
6. New suggestions for follow-up appear below response

**Visual Feedback:**
- Loading indicator while AI responds (animated dots or skeleton)
- Smooth scroll to new messages
- Input clears after send
- Send button disabled state while processing

## Accessibility
- Proper semantic HTML (main, section, article for messages)
- ARIA labels for icon buttons
- Focus states on all interactive elements
- Keyboard navigation support
- Sufficient contrast ratios for Korean text readability

## Mobile-First Approach
Design mobile layout first, then enhance for desktop:
- Mobile: Single column, full-width bubbles with max-w
- Desktop: Centered chat container with generous side margins
- Sticky elements work on both (header, categories, input)