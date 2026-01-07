# Item Gallery - React Application

A modern, responsive React application that displays items in an interactive card-based layout with expandable descriptions.

## Features

- **Fixed Navbar**: Contains title and category navigation that stays at the top while scrolling
- **Multi-Page Routing**: Separate home page and category-specific pages using React Router
- **Home Page**: Welcome section with category cards for easy navigation
- **Interactive Item Cards**: Click any card to expand and view detailed description
- **Score System**: Each item displays a score out of 100 with a color-coded progress bar
- **External Links**: Items can have links to external resources or details pages
- **Responsive Grid Layout**: Automatically adjusts to different screen sizes
- **Smooth Animations**: Hover effects and transitions for better user experience
- **Footer**: Basic footer with links and copyright information
- **Mock API Integration**: Simulates backend API data (ready to connect to real API)

## Project Structure

```
src/
├── components/
│   ├── Navbar.jsx          # Fixed navigation bar with routing
│   ├── Navbar.css
│   ├── ItemCard.jsx        # Expandable card with score & link
│   ├── ItemCard.css
│   ├── Footer.jsx          # Footer component
│   └── Footer.css
├── pages/
│   ├── Home.jsx            # Home page with intro and categories
│   ├── Home.css
│   ├── CategoryPage.jsx    # Category-specific item display
│   └── CategoryPage.css
├── App.jsx                 # Main app with routing setup
├── App.css
├── index.css               # Global styles
└── main.jsx                # Application entry point
```

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn

### Installation

Dependencies are already installed. If you need to reinstall:

```bash
npm install
```

### Running the Application

Start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:5173/`

### Building for Production

```bash
npm run build
```

The production-ready files will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Connecting to Real API

To connect to your backend API, replace the mock data in `CategoryPage.jsx`:

```javascript
// Replace this useEffect in CategoryPage.jsx
useEffect(() => {
  // Replace with your actual API endpoint
  fetch(`/api/items?category=${categoryName}`)
    .then(res => res.json())
    .then(data => setItems(data))
    .catch(error => console.error('Error fetching items:', error));
}, [categoryName]);
```

Your API should return an array of items with this structure:

```javascript
[
  {
    id: 1,
    name: "Item Name",
    description: "Item description or summary",
    category: "electronics", // lowercase category name
    score: 85, // Score out of 100 (0-100)
    link: "https://example.com/item-details" // Optional external link
  }
]
```

### Item Properties

- **id**: Unique identifier (required)
- **name**: Item name displayed in the card header (required)
- **description**: Detailed description shown when card is expanded (required)
- **category**: Category name in lowercase for filtering (required)
- **score**: Numerical score from 0-100, displayed as a progress bar (optional, defaults to 0)
- **link**: External URL shown as "View Details" button when card is expanded (optional)

## Customization

### Changing Colors

Edit the CSS files in `src/components/` to customize:
- Navbar background: `.navbar` in `Navbar.css`
- Card hover color: `.item-card:hover` in `ItemCard.css`
- Footer background: `.footer` in `Footer.css`

### Adding Categories

Modify the `categories` array in `App.jsx`:

```javascript
const categories = ['All', 'Category1', 'Category2', ...];
```

## Technologies Used

- **React 18**: UI library
- **Vite**: Build tool and dev server
- **CSS3**: Styling with animations
- **ES6+**: Modern JavaScript

## License

This project is open source and available under the MIT License.
