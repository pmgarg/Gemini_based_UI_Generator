# Idea-to-UI Generator

Transform natural language descriptions into working HTML/CSS prototypes using Google Gemini AI. Users provide their own API keys directly in the interface - no configuration needed!

## 🚀 Quick Start

python3 -m venv venv
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null


### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

### 3. Open in Browser

Navigate to `http://localhost:5000`

### 4. Connect Your API Key

1. Get your free Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Enter the key in the interface
3. Click "Connect"
4. Start generating!

## ✨ Features

### Secure API Key Handling
- **No Storage**: API keys are never saved to disk
- **Session-Only**: Keys exist only for your current session
- **User-Controlled**: Disconnect anytime to clear your key
- **Direct Input**: No environment variables or config files needed

### AI-Powered Generation
- Uses Google Gemini Pro model
- Generates complete, self-contained HTML/CSS/JS
- Creates responsive, modern designs
- Includes animations and interactions

### Live Preview
- Instant rendering of generated code
- Real-time updates
- Full-page preview in iframe
- Mobile-responsive output

### Export Options
- View generated source code
- Download as HTML file
- Copy code for your projects
- All code is self-contained (no dependencies)

## 📝 How It Works

### Step 1: Connect Your API Key
- The app starts with an API key input screen
- Enter your Gemini API key
- The app validates the key with a test request
- Once connected, the main interface appears

### Step 2: Describe Your UI
Enter a natural language description of what you want:

**Simple Example:**
```
Create a contact form with name, email, and message fields
```

**Detailed Example:**
```
Build a modern dashboard with:
- Dark sidebar with navigation menu
- Top header with search bar and user profile
- Three metric cards showing sales, revenue, and customers
- Line chart showing monthly trends
- Recent transactions table
Use a purple and blue color scheme with smooth animations
```

### Step 3: Generate
- Click "Generate UI" button
- Gemini processes your description
- HTML/CSS/JS code is generated
- Preview appears instantly

### Step 4: Export
- View the complete source code
- Download as an HTML file
- Use in your projects

## 🎨 Example Descriptions

### Dashboard
```
Create a financial dashboard with a dark sidebar containing menu items 
for Overview, Analytics, Reports, and Settings. The main area should 
display three colorful metric cards, a line chart for revenue trends, 
and a recent transactions table.
```

### Landing Page
```
Design a SaaS landing page with:
- Sticky navigation bar with logo and menu
- Hero section with gradient background, headline, and CTA buttons
- Features grid with icons and descriptions
- Pricing table with three tiers
- Testimonials carousel
- Footer with newsletter signup
```

### E-commerce Product Page
```
Build a product page with:
- Large image gallery on the left with thumbnails
- Product details on the right (title, price, description)
- Size and color selectors
- Quantity selector and add to cart button
- Customer reviews section with star ratings
- Related products carousel at the bottom
```

### Portfolio Website
```
Create a developer portfolio with:
- Animated hero section with name and title
- About section with skills badges
- Projects grid with hover effects showing details
- Experience timeline
- Contact form with validation
- Dark mode with neon accents
```

## 🔧 Customization

### Using Different Models

While the app is configured for Gemini Pro, you can modify it for other models:

```python
# In generate_ui_code function, change the model:
model = genai.GenerativeModel('gemini-1.5-flash')  # For faster generation
```

### Adjusting the Prompt

The generation prompt in `generate_ui_code()` can be customized:

```python
prompt = f"""
    Your custom instructions here...
    {description}
    Additional requirements...
"""
```

### Styling the Interface

Modify the embedded CSS in `HTML_TEMPLATE` to change colors, fonts, or layout.

## 🛡️ Security Features

1. **No Server Storage**: API keys are never written to disk
2. **HTTPS Recommended**: Use HTTPS in production
3. **Session Isolation**: Each user's key is isolated
4. **Clear Disconnect**: Users can clear their key anytime
5. **No Logs**: API keys aren't logged

## 📊 API Usage & Limits

### Gemini API Free Tier
- 60 requests per minute
- Free for most use cases
- No credit card required

### Tips for Optimal Usage
- Be specific in descriptions for better results
- Use the examples as templates
- Iterate on descriptions for refinement
- Combine multiple attempts for complex UIs

## 🚨 Troubleshooting

### "Invalid API Key" Error
- Verify key is copied correctly (no extra spaces)
- Check key permissions in Google AI Studio
- Ensure key is for Gemini API (not other Google services)

### Generation Takes Too Long
- Simplify your description
- Break complex UIs into parts
- Check your internet connection

### Generated UI Doesn't Match Description
- Make description more specific
- Include design details (colors, layout)
- Use technical terms when needed
- Try regenerating with refined description

### Preview Not Loading
- Check browser console for errors
- Ensure JavaScript is enabled
- Try a different browser

## 🎯 Best Practices

### For Better Results
1. **Be Specific**: Include colors, layouts, and styling preferences
2. **Reference Modern Patterns**: Mention "card-based", "gradient", "glassmorphism"
3. **Include Interactions**: Specify hover effects, animations, transitions
4. **Describe Data**: Provide context for placeholder content
5. **Mention Responsive Needs**: Specify mobile behavior if important

### What Works Well
✅ UI components and layouts
✅ Landing pages and marketing sites
✅ Dashboards and admin panels
✅ Forms and data displays
✅ Portfolio and showcase sites

### Current Limitations
⚠️ Complex JavaScript applications
⚠️ Backend functionality
⚠️ Database connections
⚠️ External API integrations
⚠️ Multi-page applications (generates single pages)

## 🔄 Updates & Improvements

### Planned Features
- [ ] Support for multiple AI providers (OpenAI, Claude)
- [ ] Template library
- [ ] Code editing within the app
- [ ] Component extraction
- [ ] CSS framework options
- [ ] Multi-page generation

## 📄 License

MIT License - Free to use and modify!

## 🤝 Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Share your generated UIs

## 💡 Pro Tips

1. **Start Simple**: Begin with basic layouts, then add complexity
2. **Use Examples**: Modify the provided examples for quick starts
3. **Iterate**: Generate multiple versions and combine the best parts
4. **Learn from Output**: Study the generated code to learn HTML/CSS patterns
5. **Save Good Prompts**: Keep descriptions that work well for reuse

---
