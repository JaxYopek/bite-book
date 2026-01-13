# BiteBook

A Django-based web application for restaurant and menu item reviews, inspired by Letterboxd but for food. Users can discover restaurants, review menu items with detailed ratings, share experiences, and build flavor profiles based on their preferences.

## Features

- **User Authentication**: Sign up, log in, and manage accounts with Django's built-in auth system.
- **Restaurant Management**:
  - Add new restaurants with Google Places API autocomplete for verified addresses.
  - Search and filter restaurants by name, cuisine type, location, or happy hour availability.
  - Real-time AJAX-powered search with pagination.
  - Duplicate address prevention with validation.
  - Happy hour information display.
- **Menu Management**:
  - Create menus for restaurants.
  - Add menu items with name, description, and price.
  - View aggregate ratings for menu items.
- **Review System**:
  - Rate menu items on a scale of 1.0 to 10.0 (to one decimal place).
  - Write detailed reviews with optional images.
  - Choose to make reviews public or anonymous.
  - Like reviews from other users.
- **Posts Feed**:
  - Public reviews appear as posts on everyone's feed.
  - Create personal diary entries for general food thoughts and experiences.
  - View recent posts with ratings and review text.
- **User Profiles**:
  - Letterboxd-style profile pages with large avatars.
  - Favorite restaurants and Want to Try lists.
  - Flavor profile showing top 3 cuisine preferences.
  - Top Reviewer badge for active users.
  - Follow/unfollow other users.
- **Enhanced UI/UX**:
  - DoorDash-style category filter pills.
  - Compact restaurant cards with ratings, reviews, and happy hour badges.
  - Clickable addresses that open in Google Maps.
  - Responsive design with custom color scheme.

## Tech Stack

- **Backend**: Django 5.2.6, Python 3.13.2
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript (with AJAX for real-time filtering)
- **APIs**: Google Places API, Google Maps JavaScript API
- **Color Scheme**: #F7EDE2 (background), #5B5941 (text), #FB8B24 (accent)

## Installation

1. **Clone the repository**:
   ```bash
   git clone [<repository-url>](https://github.com/JaxYopek/bite-book.git)
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

4. **Configure Google Maps API** (required for address autocomplete):
   - Create a `config/local_settings.py` file:
     ```python
     # Local settings - DO NOT COMMIT THIS FILE
     GOOGLE_MAPS_API_KEY = 'your-api-key-here'
     ```
   - Get your API key from [Google Cloud Console](https://console.cloud.google.com/)
   - Enable these APIs: Maps JavaScript API, Places API
   - The `local_settings.py` file is already in `.gitignore` for security

5. **Run migrations**:
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

- **Home/Feed**: View recent public posts from all users. Navigation bar for easy access to features.
- **Create Post**: Write personal diary entries to share food experiences.
- **My Profile**: View your own posts and reviews.
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
