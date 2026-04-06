# Technical Documentation: Image Background Remover Application

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Database Module (db.py)](#database-module-dbpy)
4. [Main Application (login.py)](#main-application-loginpy)
5. [Technical Details](#technical-details)
6. [Dependencies](#dependencies)

---

## Overview

This is a desktop application built with Python's Tkinter framework that provides image background removal functionality with user authentication. The application features a modern, animated UI with neon-themed design elements and supports single image processing, batch processing, and history tracking.

### Key Features
- User authentication (login/signup)
- Single image background removal
- Batch processing (up to 5 images)
- Processing history with database persistence
- Animated UI with particle effects
- MySQL database integration

---

## Architecture

### Application Structure
```
login-app/
├── login.py          # Main application with UI and logic
├── db.py             # Database operations and connection management
├── .env              # Environment variables for database configuration
└── templates/        # (Empty folder for potential future use)
```

### Design Pattern
- **MVC-like Architecture**: Separation of concerns between UI (login.py) and data layer (db.py)
- **Single Window Application**: Uses frame switching instead of multiple windows
- **Threaded Processing**: Background removal runs in separate threads to prevent UI freezing

---

## Database Module (db.py)

### Purpose
Handles all database operations including connection management, user authentication, and history tracking.

### Technical Components

#### 1. Environment Configuration
```python
# Loads .env file and sets environment variables
_ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
```

**Process:**
- Reads `.env` file line by line
- Parses `KEY=VALUE` pairs
- Sets environment variables using `os.environ.setdefault()`
- Ignores comments (lines starting with `#`)

#### 2. Database Configuration
```python
DB_CONFIG = {
    "host":     os.environ.get("MYSQL_HOST",     "localhost"),
    "port":     int(os.environ.get("MYSQL_PORT", "3306")),
    "user":     os.environ.get("MYSQL_USER",     "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.environ.get("MYSQL_DATABASE", "image_editor"),
}
```

**Configuration Parameters:**
- `MYSQL_HOST`: Database server address (default: localhost)
- `MYSQL_PORT`: Database port (default: 3306)
- `MYSQL_USER`: Database username (default: root)
- `MYSQL_PASSWORD`: Database password (default: empty)
- `MYSQL_DATABASE`: Database name (default: image_editor)

#### 3. Database Schema

**Users Table:**
```sql
CREATE TABLE IF NOT EXISTS users (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(64) NOT NULL
);
```
- `id`: Auto-incrementing primary key
- `username`: Unique username (max 50 characters)
- `password`: SHA-256 hashed password (64 characters)

**History Table:**
```sql
CREATE TABLE IF NOT EXISTS history (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(50) NOT NULL,
    input_path  TEXT NOT NULL,
    output_path TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```
- `id`: Auto-incrementing primary key
- `username`: User who performed the operation
- `input_path`: Path to original image
- `output_path`: Path to processed image (nullable)
- `created_at`: Timestamp of operation

#### 4. Core Functions

**`_hash(password: str) -> str`**
- Uses SHA-256 algorithm to hash passwords
- Returns 64-character hexadecimal string
- Security: One-way hashing prevents password recovery

**`get_connection()`**
- Creates and returns MySQL connection using `DB_CONFIG`
- Uses `mysql.connector.connect()`
- Returns connection object for database operations

**`init_db()`**
- Initializes database and tables
- Creates database if it doesn't exist
- Executes schema SQL statements
- Creates default admin user (username: "admin", password: "1234")
- **Process:**
  1. Connect without specifying database
  2. Create database if needed
  3. Switch to the database
  4. Execute table creation statements
  5. Check for admin user and create if missing

**`validate_user(username: str, password: str) -> bool`**
- Validates user credentials
- Hashes input password and compares with stored hash
- Returns `True` if credentials match, `False` otherwise
- Raises `ConnectionError` on database errors

**`register_user(username: str, password: str) -> tuple[bool, str]`**
- Registers new user account
- Returns tuple: (success_boolean, message_string)
- **Validation:**
  - Checks for empty username/password
  - Handles duplicate username (IntegrityError)
  - Hashes password before storage
- **Return Values:**
  - `(True, "Account created successfully.")` on success
  - `(False, "Username already exists.")` on duplicate
  - `(False, "Username and password are required.")` on empty fields
  - `(False, "DB error: {error}")` on database errors

**`add_history(username: str, input_path: str, output_path: str) -> None`**
- Records image processing operation
- Silently fails on errors (uses `pass` in except block)
- Stores username, input path, output path, and timestamp

**`get_history(username: str) -> list`**
- Retrieves processing history for a user
- Returns list of tuples: `(id, input_path, output_path, created_at)`
- Ordered by `created_at DESC` (newest first)
- Returns empty list on errors

---

## Main Application (login.py)

### Class: LoginApp(tk.Tk)

Main application class inheriting from `tk.Tk` (Tkinter root window).

### Initialization (`__init__`)

**Window Configuration:**
- Title: "Image Background Remover"
- Background: Dark theme (`#0d0d0d`)
- Resizable: True
- Initial size: 480x660 (login) / 980x680 (dashboard)

**Instance Variables:**
- `_alpha`: Fade-in animation opacity (0.0 to 1.0)
- `_current_user`: Currently logged-in username
- `_orig_image`: Original image (PIL Image object)
- `_result_image`: Processed image with background removed
- `_history`: In-memory list of processing operations
- `_particles`: List of particle objects for animation
- `_logo_pulse`: Logo animation state (0.0 to 1.0)
- `_logo_growing`: Logo animation direction boolean
- `_subtitle_idx`: Current subtitle text index
- `_subtitle_texts`: List of rotating subtitle messages

**Initialization Sequence:**
1. Build fonts
2. Build authentication UI
3. Center window
4. Start fade-in animation
5. Initialize database

### Color Palette

```python
BG        = "#0d0d0d"  # Background (very dark gray)
CARD      = "#1a1a1a"  # Card background (dark gray)
BORDER    = "#2a2a2a"  # Border color (medium dark gray)
NEON      = "#39ff14"  # Primary neon green
NEON_DIM  = "#27b30d"  # Dimmed neon green
NEON_DARK = "#0d3d05"  # Dark neon green
TEXT      = "#e0e0e0"  # Primary text (light gray)
SUBTEXT   = "#888888"  # Secondary text (medium gray)
ERROR_CLR = "#ff4444"  # Error messages (red)
SUCCESS   = "#39ff14"  # Success messages (neon green)
```

### Font System

**Font Definitions:**
- `f_title`: Segoe UI, 22pt, bold (main titles)
- `f_sub`: Segoe UI, 9pt (subtitles and small text)
- `f_label`: Segoe UI, 10pt, bold (form labels)
- `f_entry`: Segoe UI, 11pt (input fields)
- `f_btn`: Segoe UI, 11pt, bold (buttons)
- `f_link`: Segoe UI, 9pt, underline (links)
- `f_dash_title`: Segoe UI, 18pt, bold (dashboard title)
- `f_dash_sub`: Segoe UI, 10pt (dashboard subtitle)
- `f_card_title`: Segoe UI, 12pt, bold (card titles)
- `f_logo`: Segoe UI, 18pt, bold (logo text)
- `f_subtitle`: Segoe UI, 10pt (subtitle text)

---

## Authentication UI System

### Frame Hierarchy
```
self (Tk root)
└── auth_root (Frame)
    ├── bg_canvas (Canvas) - Background with particles
    └── card_frame (Frame) - Centered login/signup card
        ├── login_frame (Frame)
        └── signup_frame (Frame)
```

### Particle Animation System

**Particle Properties:**
- Count: 38 particles (`NUM_PARTICLES`)
- Each particle has:
  - `x, y`: Position coordinates
  - `r`: Radius (1.5 to 4 pixels)
  - `vx, vy`: Velocity (horizontal and vertical)
  - `alpha`: Opacity (0.3 to 1.0)
  - `fade`: Fade direction and speed

**Animation Logic (`_animate_particles`):**
1. Clear previous particles
2. Update each particle:
   - Move by velocity
   - Update alpha (fade in/out)
   - Wrap around screen edges
3. Draw particles as circles with glow effect
4. Draw grid lines (60px spacing)
5. Schedule next frame (30ms delay)

**Visual Effects:**
- Particles drift upward and sideways
- Pulsing opacity creates twinkling effect
- Grid overlay adds depth
- Green color matches neon theme

### Logo Pulse Animation

**Algorithm (`_animate_logo_pulse`):**
```python
# Sine wave interpolation for smooth pulsing
t = (math.sin(self._logo_pulse * math.pi) + 1) / 2
r = int(0x27 + (0x39 - 0x27) * t)  # Red channel
g = int(0xb3 + (0xff - 0xb3) * t)  # Green channel
b = int(0x0d + (0x14 - 0x0d) * t)  # Blue channel
```

- Oscillates between `NEON_DIM` and `NEON` colors
- Uses sine wave for smooth transition
- Updates every 40ms
- Creates breathing effect on logo

### Typewriter Subtitle Animation

**Process (`_animate_subtitle`, `_type_text`):**
1. Select next subtitle from rotation
2. Type characters one by one (45ms delay)
3. Wait 2800ms after completion
4. Repeat with next subtitle

**Subtitle Messages:**
- "Remove backgrounds instantly ✨"
- "Fast. Clean. Precise. 🎯"
- "Sign in to get started →"

### Login Frame Components

**Structure:**
1. Neon accent bar (3px height)
2. Logo with pulse animation
3. Typewriter subtitle
4. "Sign in to your account" text
5. Divider line
6. Username field with icon
7. Password field with show/hide toggle
8. Error message label
9. Login button (neon style)
10. Divider line
11. "Create an account" button (ghost style)

**Password Toggle:**
- Eye icon (👁) shows password
- Eye with speech bubble (👁‍🗨️) hides password
- Uses `show="●"` parameter for masking

### Signup Frame Components

Similar structure to login frame with:
- Different title: "Create your account"
- Different subtitle: "Fill in the details below"
- Signup button instead of login
- "Back to login" button

---

## Dashboard System

### Frame Hierarchy
```
self (Tk root)
└── dash_root (Frame)
    ├── nav (Frame) - Top navigation bar
    ├── body (Frame)
    │   ├── sidebar (Frame) - Tool buttons
    │   └── editor_frame / batch_frame / history_frame
    └── status_bar (Label) - Bottom status
```

### Navigation Bar

**Components:**
- Logo and title
- Greeting message: "Welcome back, {username} 👋"
- Logout button with hover effects

**Logout Button Behavior:**
- Hover: Background changes to `BORDER`
- Click: Destroys and rebuilds auth UI, returns to login

### Sidebar Tools

**Tool Buttons:**
1. 🖼️ Remove BG - Single image processing
2. 📁 Batch - Multiple image processing (max 5)
3. 🕓 History - View processing history

**Button Styling:**
- Flat design with no borders
- Hover effect: Background → `BORDER`, Text → `NEON`
- Left-aligned text with icons

### Editor Panel

**Layout:**
- Two-column grid for Original and Result
- Canvas widgets for image preview (340x280)
- Three action buttons:
  - 📂 Open Image
  - ✨ Remove Background (disabled until image loaded)
  - 💾 Save Result (disabled until processing complete)
- Progress bar (hidden by default)

**Image Preview System:**
- Maintains aspect ratio
- Centers image in canvas
- Checkerboard background for transparent images
- Placeholder text when empty

---

## Background Removal System

### Process Flow

**1. Image Selection (`_on_remove_bg`):**
- Opens file dialog
- Supported formats: PNG, JPG, JPEG, WEBP, BMP
- Loads image as RGBA
- Displays in original canvas
- Enables "Remove Background" button

**2. Processing (`_run_remove_bg`):**
- Disables all buttons
- Shows progress bar with animation
- Starts background thread
- Updates status message

**3. Background Thread (`_bg_remove_thread`):**
- Calls `rembg_remove()` function
- Uses `self.after(0, ...)` to update UI from main thread
- Handles exceptions and reports errors

**4. Completion (`_on_remove_done`):**
- Stores result image
- Stops progress animation
- Displays result with checkerboard background
- Re-enables buttons
- Adds to history (database and memory)

**5. Saving (`_on_save`):**
- Opens save dialog with default name: `{original}_nobg.png`
- Saves as PNG with transparency
- Updates history with output path
- Updates status message

### Progress Animation

**Algorithm (`_animate_progress`):**
```python
pos = (pos + 0.015) % 1.0
fill = 0.3 + 0.3 * abs(pos * 2 - 1)
```

- Creates pulsing effect (30% to 60% width)
- Updates every 30ms
- Stops when `_stop_progress` flag is set

---

## Batch Processing System

### Workflow

**1. Image Selection:**
- Multi-select file dialog
- Maximum 5 images enforced
- Shows warning if limit exceeded

**2. Panel Creation (`_show_batch_panel`):**
- Destroys previous batch frame if exists
- Creates scrollable interface
- Displays input thumbnails (160x160)
- Creates output placeholders

**3. Processing (`_batch_panel_thread`):**
- Creates `nobg_output` folder in source directory
- Processes images sequentially
- Updates progress bar and status
- Updates output cells with results
- Runs in background thread

**4. Output Display (`_update_output_cell`):**
- Shows processed thumbnail with checkerboard
- Displays filename
- Adds download button for each image

### Batch Panel Layout

**Components:**
- Top bar: Title, status, back button
- Progress bar (fills as processing completes)
- Scrollable content area:
  - Column headers
  - Input row with thumbnails
  - Output row with results/status
- Process All button

**Status Messages:**
- "⏳ Pending" - Not yet processed
- "⚙ Processing…" - Currently processing
- "✗ Error" - Processing failed
- Thumbnail + filename - Success

---

## History System

### Data Flow

**Storage:**
- Database: Persistent storage via `db.add_history()`
- Memory: `self._history` list for current session

**Retrieval:**
- Queries database: `db.get_history(username)`
- Returns: `(id, input_path, output_path, created_at)`
- Ordered by date (newest first)

### History Panel

**Layout:**
- Top bar with record count and back button
- Scrollable table with columns:
  - # (row number)
  - INPUT (thumbnail + filename)
  - OUTPUT (thumbnail + filename + download button)
  - DATE (timestamp)

**Row Styling:**
- Alternating backgrounds: `CARD` and `#1f1f1f`
- Borders between rows
- Thumbnails: 120x120 pixels

**Thumbnail Display (`_hist_thumb`):**
- Loads image from path
- Resizes to fit
- Applies checkerboard for transparent images
- Shows filename next to thumbnail
- Handles missing files gracefully

---

## Helper Functions and Utilities

### Image Processing Helpers

**`_show_preview(canvas, img, checkerboard=False)`**
- Displays image in canvas
- Maintains aspect ratio
- Optional checkerboard background for transparency
- Centers image in canvas

**`_make_checker(w, h, size=12)`**
- Creates checkerboard pattern
- Alternates between light gray (200,200,200) and medium gray (150,150,150)
- Configurable square size (default 12px)
- Returns PIL Image object

**`_draw_placeholder(canvas, text)`**
- Displays centered text in empty canvas
- Used for "Click to open" messages
- Styled with `SUBTEXT` color

**`_animate_progress(pos)`**
- Animates progress bar with pulsing effect
- Recursive function using `self.after()`
- Stops when `_stop_progress` flag is True

### Widget Builders

**`_neon_button(parent, text, cmd, row)`**
- Creates primary action button
- Neon green background
- Hover effect: Dims to `NEON_DIM`
- Full width with padding

**`_ghost_button(parent, text, cmd, row)`**
- Creates secondary action button
- Transparent with neon border
- Hover effect: Dark neon background
- Full width with padding

**`_neon_btn_small(parent, text, cmd, col)`**
- Creates small action button for dashboard
- Used in editor panel
- Grid layout instead of full width

**`_styled_entry(parent, var, row, show="", container=None)`**
- Creates styled text input field
- Dark background with neon highlights
- Focus effects: Border changes to neon
- Optional password masking

**`_field_label(parent, text, row)`**
- Creates form field label
- Neon dim color
- Left-aligned with icon support

**`_divider(parent, row)`**
- Creates horizontal separator line
- 1px height, `BORDER` color
- Full width with padding

### Animation and Effects

**`_fade_in()`**
- Gradually increases window opacity
- Starts at 0.0, increments by 0.05
- Updates every 20ms
- Creates smooth appearance effect

**`_shake(widget, count=6, delta=6)`**
- Shakes widget horizontally
- Used for error feedback
- 6 oscillations by default
- 6px displacement

**`_toggle_pass(lbl, entry, var)`**
- Toggles password visibility
- Updates entry `show` parameter
- Changes icon between 👁 and 👁‍🗨️

### Window Management

**`_center_window(w, h)`**
- Centers window on screen
- Calculates screen dimensions
- Sets geometry: `{w}x{h}+{x}+{y}`

**`_place_card()`**
- Positions login/signup card in center
- Calculates based on auth_root size
- Card size: 380px wide, max 600px tall
- Called on window resize

**`_on_auth_resize(event)`**
- Event handler for window resize
- Calls `_place_card()` to reposition

### View Switching

**`_switch_to(view)`**
- Switches between login and signup frames
- Clears all input fields
- Clears error messages
- Raises appropriate frame using `tkraise()`

**`_show_dashboard(username)`**
- Hides auth UI
- Resizes window to 980x680
- Shows or creates dashboard
- Updates greeting message

**`_show_editor_panel()`**
- Hides batch and history frames
- Shows editor frame
- Used when returning from other tools

**`_close_history_panel()`**
- Hides history frame
- Shows editor frame

---

## Authentication Logic

### Login Process (`_on_login`)

**Validation:**
1. Strip whitespace from inputs
2. Check for empty fields
3. Show error and shake button if invalid

**Authentication:**
1. Call `db.validate_user(username, password)`
2. If valid: Show dashboard
3. If invalid: Show error message and shake button
4. Handle database errors with error message

### Signup Process (`_on_signup`)

**Registration:**
1. Strip whitespace from inputs
2. Call `db.register_user(username, password)`
3. Display success/error message
4. If successful: Wait 800ms, then redirect to login page

**Validation (in db.py):**
- Empty field check
- Duplicate username check
- Database error handling

### Logout Process (`_on_logout`)

**Cleanup:**
1. Clear current user
2. Clear image data
3. Hide dashboard
4. Destroy and rebuild auth UI (ensures clean state)
5. Resize window to 480x660
6. Switch to login view

**Why Rebuild Auth UI:**
- Ensures all animations restart
- Clears any residual state
- Repositions card correctly
- Reinitializes particle system

---

## Technical Details

### Threading Model

**Main Thread:**
- UI rendering and event handling
- All Tkinter operations
- Animation loops

**Background Threads:**
- Image processing (`_bg_remove_thread`)
- Batch processing (`_batch_panel_thread`)

**Thread Safety:**
- Uses `self.after(0, callback)` to update UI from background threads
- Ensures all Tkinter operations run on main thread
- Daemon threads automatically terminate when app closes

### Memory Management

**Image References:**
- `self._orig_image`: Original PIL Image
- `self._result_image`: Processed PIL Image
- `self._batch_thumb_refs`: List of PhotoImage objects (prevents garbage collection)
- `self._hist_thumb_refs`: List of PhotoImage objects for history

**Why Store PhotoImage References:**
- Tkinter's PhotoImage objects are garbage collected if not referenced
- Storing in list prevents premature deletion
- Images would disappear from UI without references

### Geometry Managers

**Grid:**
- Used for structured layouts (forms, tables)
- Login/signup frames
- Dashboard navigation and body

**Pack:**
- Used for sequential layouts
- Sidebar buttons
- Batch processing rows

**Place:**
- Used for absolute positioning
- Background canvas (fullscreen)
- Login/signup card (centered)
- Progress bar fill (animated width)

### Error Handling

**Database Errors:**
- Caught and displayed to user
- Connection errors shown in login form
- History operations fail silently

**Image Processing Errors:**
- Caught in background thread
- Displayed via messagebox
- Status updated to show error

**File Operations:**
- Try-except blocks for image loading
- Graceful degradation (show placeholder on error)

---

## Dependencies

### Required Libraries

**Standard Library:**
- `tkinter`: GUI framework
- `threading`: Background processing
- `random`: Particle animation
- `math`: Logo pulse animation
- `shutil`: File operations
- `os`: Path and environment operations
- `hashlib`: Password hashing

**Third-Party:**
- `Pillow (PIL)`: Image processing
  - `Image`: Image manipulation
  - `ImageTk`: Tkinter image display
- `mysql-connector-python`: MySQL database connectivity
- `rembg`: Background removal (optional)
  - Uses AI model to remove backgrounds
  - Gracefully degrades if not installed

### Installation

```bash
pip install pillow mysql-connector-python rembg
```

### Database Requirements

- MySQL Server 5.7 or higher
- Database: `image_editor` (auto-created)
- User with CREATE, INSERT, SELECT permissions

---

## Configuration

### Environment Variables (.env)

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=image_editor
```

### Default Credentials

**Admin Account:**
- Username: `admin`
- Password: `1234`
- Created automatically on first run

---

## Performance Considerations

### Optimization Techniques

**1. Lazy Loading:**
- Dashboard built only when first accessed
- Batch/history frames created on demand

**2. Image Thumbnailing:**
- All previews use thumbnails, not full-size images
- Reduces memory usage
- Improves rendering speed

**3. Animation Throttling:**
- Particles: 30ms delay (33 FPS)
- Logo pulse: 40ms delay (25 FPS)
- Progress: 30ms delay (33 FPS)

**4. Thread Usage:**
- Heavy processing in background threads
- UI remains responsive during processing

### Memory Usage

**Typical Memory Footprint:**
- Base application: ~50-100 MB
- Per image loaded: +image size
- Batch processing: +5x image sizes (temporary)

---

## Security Considerations

### Password Security

**Hashing:**
- SHA-256 algorithm
- One-way hashing (cannot be reversed)
- No salt (consider adding for production)

**Recommendations for Production:**
- Use bcrypt or Argon2 instead of SHA-256
- Add salt to prevent rainbow table attacks
- Implement password strength requirements
- Add rate limiting for login attempts

### Database Security

**Current Implementation:**
- Credentials in .env file
- No SQL injection protection (uses parameterized queries)

**Recommendations:**
- Use environment variables or secure vault
- Implement connection pooling
- Add database user with minimal permissions
- Enable SSL for database connections

### File System Security

**Current Implementation:**
- Saves files to user-selected locations
- No path validation

**Recommendations:**
- Validate file paths
- Restrict file types
- Implement file size limits
- Scan uploaded files for malware

---

## Known Limitations

1. **Batch Processing:**
   - Limited to 5 images
   - Sequential processing (not parallel)
   - No progress for individual images

2. **History:**
   - No pagination (loads all records)
   - No search or filter functionality
   - File paths may become invalid if files moved

3. **Authentication:**
   - No password recovery
   - No email verification
   - No session timeout
   - No "remember me" functionality

4. **Image Processing:**
   - Requires rembg library
   - No undo functionality
   - No image editing features
   - No format conversion options

5. **UI:**
   - Fixed minimum window size
   - No dark/light theme toggle
   - No keyboard shortcuts
   - No accessibility features

---

## Future Enhancement Opportunities

1. **Authentication:**
   - Password reset via email
   - Two-factor authentication
   - OAuth integration
   - Session management

2. **Image Processing:**
   - Multiple AI models
   - Manual editing tools
   - Batch processing improvements
   - Format conversion

3. **UI/UX:**
   - Drag-and-drop support
   - Keyboard shortcuts
   - Theme customization
   - Accessibility improvements

4. **Performance:**
   - Parallel batch processing
   - Image caching
   - Database connection pooling
   - Lazy loading for history

5. **Features:**
   - Cloud storage integration
   - Image filters and effects
   - Bulk export options
   - Processing presets

---

## Troubleshooting

### Common Issues

**1. "rembg is not installed" Error:**
- Install: `pip install rembg`
- Requires internet for first-time model download

**2. Database Connection Failed:**
- Check MySQL server is running
- Verify credentials in .env file
- Ensure database user has proper permissions

**3. Black Screen on Logout:**
- Fixed in latest version
- Auth UI is destroyed and rebuilt on logout

**4. Images Not Displaying:**
- Check file paths are valid
- Ensure Pillow is installed correctly
- Verify image format is supported

**5. Slow Performance:**
- Reduce number of particles (NUM_PARTICLES)
- Close other applications
- Use smaller images for testing

---

## Code Metrics

**Total Lines:** ~999 lines
**Classes:** 1 (LoginApp)
**Functions:** ~50 methods
**Database Tables:** 2 (users, history)
**UI Frames:** 5 (auth, login, signup, dashboard, editor/batch/history)

---

## Conclusion

This application demonstrates a complete desktop application with:
- Modern, animated UI
- Database integration
- Multi-threaded processing
- User authentication
- File management
- Error handling

The codebase is well-structured with clear separation of concerns, making it maintainable and extensible for future enhancements.
