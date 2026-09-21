# System Architecture Specification

**Project**: ecom
**Target Goal**: Here is a comprehensive prompt you can use to generate a simple, fully functional single-page E-commerce website:

---

### **Prompt**

"Generate a complete, modern, and responsive single-page E-commerce website using **HTML, CSS, and Vanilla JavaScript** (all in a single integrated HTML file).

The website should include the following core features:

1. **Header & Navigation:**
   * Brand name/logo on the left.
   * Search bar in the center to filter products by name.
   * Category filter buttons (e.g., 'All', 'Electronics', 'Clothing', 'Accessories').
   * Cart icon on the right with a dynamic item counter badge.

2. **Product Grid / Catalog:**
   * A responsive grid of product cards (at least 6-8 sample products with mock data).
   * Each card must display: Product Image (via Unsplash placeholder), Title, Category, Price, and an 'Add to Cart' button.

3. **Interactive Shopping Cart:**
   * A slide-over drawer or modal that opens when the Cart icon is clicked.
   * Displays added items with: Thumbnail, Title, Unit Price, Quantity controls (+ / -), Item total, and a 'Remove' button.
   * Dynamic calculation of Subtotal, Tax (e.g., 8%), and Grand Total.
   * A 'Checkout' button that opens a simple confirmation modal.

4. **Checkout Modal:**
   * Simple form with fields for: Name, Email, Shipping Address, and a dummy 'Pay Now' button.
   * Submitting clears the cart and displays a success alert.

5. **Design & UX:**
   * Modern, clean UI with a professional color palette (e.g., dark slate header, light background, vibrant action buttons).
   * Smooth hover effects on buttons and cards.
   * Fully responsive across mobile, tablet, and desktop screens."

## 1. System Overview
Self-contained reactive single-page architecture with decoupled presentation and state layers.

## 2. Component Structure
- **UI Layer**: Semantic HTML5 with responsive flex/grid styling.
- **Logic Controller**: Interactive JavaScript event loop handling user inputs and state.
- **Validation**: Sanitized input handlers with defensive boundary checking.
