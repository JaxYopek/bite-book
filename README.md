# BiteBook

A Django-based web application for restaurant and menu item reviews, inspired by Letterboxd but for food. Users can discover restaurants, review menu items with detailed ratings, and share their experiences on a public feed.

## Features

- **User Authentication**: Sign up, log in, and manage accounts with Django's built-in auth system.
- **Restaurant Management**:
  - Add new restaurants with unique address validation.
  - Search and filter restaurants by name, cuisine type, or location.
  - Real-time AJAX-powered search with pagination.
- **Menu Management**:
  - Create menus for restaurants.
  - Add menu items with name, description, and price.
- **Review System**:
  - Rate menu items on a scale of 1.0 to 10.0 (to one decimal place).
  - Write detailed reviews.
  - Choose to make reviews public or anonymous.
- **Posts Feed**:
  - Public reviews appear as posts on everyone's feed.
  - Posts have descriptive titles (e.g., "username reviewed item at restaurant").
  - View recent posts with ratings and review text.

## Tech Stack

- **Backend**: Django 5.2.6
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript (with AJAX for real-time search)
- **Other**: Google Places API (commented out for potential location autocomplete)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd bite-book
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser (optional)**:
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

7. **Access the app**:
   - Open your browser to `http://127.0.0.1:8000/`
   - Sign up or log in to start exploring restaurants and reviews.

## Usage

- **Home/Feed**: View recent public posts from all users.
- **Restaurants**: Search for restaurants, add new ones, or view details.
- **Menus**: For each restaurant, view or add menu items.
- **Reviews**: Rate and review menu items; public reviews appear on the feed.
- **Admin Panel**: Access at `/admin/` (requires superuser) to manage data.

## Project Structure

```
bite-book/
├── config/                 # Django settings and URLs
├── restaurants/            # Main app for restaurants, menus, reviews
├── posts/                  # App for public review posts
├── templates/              # HTML templates
├── static/                 # Static files (CSS, JS)
├── db.sqlite3              # SQLite database
├── manage.py               # Django management script
└── requirements.txt        # Python dependencies
```

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Make your changes and test thoroughly.
4. Submit a pull request.

## License

This project is licensed under the MIT License. See LICENSE for details.