#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from operator import add
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

""" 
export FLASK_APP=myapp 
export FLASK_ENV=development
python app.py 
"""

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

#db.create_all()
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

from models import *

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format="EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format="EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html', data=[])

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    locations_query = Venue.query.with_entities(func.count(Venue.id), Venue.city, Venue.state).group_by(Venue.city, Venue.state).order_by(Venue.city).all()
    if not locations_query:
        abort(404)
    else:
        locations = locations_query
    
    view_data = []
    for location in locations:
        venue_query = Venue.query.filter(Venue.state == location.state).filter(Venue.city == location.city) 
        venues_list = []
        for venue in venue_query:
            if(venue.city == location.city and venue.state == location.state):
                venues_list.append({
                  'id': venue.id,
                  'name': venue.name,
                  'num_upcoming_shows': len(db.session.query(Show).filter(Show.start_time > datetime.now()).all())
                })
        view_data.append({
          'city': location.city,
          'state': location.state,
          'venues': venues_list
        })
    return render_template('pages/venues.html', areas=view_data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
    venue_search_term = request.form.get('search_term', '')
    venue_search_query = db.session.query(Venue).filter(Venue.name.ilike(f'%{venue_search_term}%')).all()
    results_list = []
    for venue_result in venue_search_query:
      results_list.append({
        'id': venue_result.id,
        'name': venue_result.name,
        'num_upcoming_shows': len(db.session.query(Show).filter(Show.venue_id == venue_result.id).filter(Show.start_time > datetime.now()).all())
      })

    venue_search_results_data = {
      'count': len(results_list),
      'data': results_list
    }
    return render_template('pages/search_venues.html', results=venue_search_results_data, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue_query = Venue.query.get(venue_id)

    if not venue_query:
        abort(404)
    else: venue = venue_query

    upcoming_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
    upcoming_shows = []

    past_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()
    past_shows = []

    for show in past_shows_query:
      past_shows.append({
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })

    for show in upcoming_shows_query:
      upcoming_shows.append({
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")    
      })
    shows_view_data = {
      "id": venue.id,
      "name": venue.name,
      "genres": venue.genres,
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_venue.html', venue=shows_view_data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    print('form: ', request.form)
    try:
        venue = Venue(
            name = request.form['name'],
            city = request.form['city'],
            state = request.form['state'],
            address = request.form['address'],
            phone = request.form['phone'],
            genres = request.form.getlist('genres'),
            image_link = request.form['image_link'],
            facebook_link = request.form['facebook_link'],
            website = request.form['website_link'],
            seeking_talent = True if 'seeking_talent' in request.form else False,
            seeking_description = request.form['seeking_description']
        )
        print('venue', venue)
        db.session.add(venue)
        db.session.commit()
        flash('Venue' + request.form['name'] + 'was successfully created')
    except Exception as err:
        print(err)
        flash('There was an error. Venue ' + request.form['name'] + ' could not be added. Please try again.')
        db.session.rollback()
    finally:
        db.session.close()
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # I completed the bonus challenge and implemented a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it via the endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record.
    print('delete venue', venue_id)
    try:
      venue = Venue.query.get(venue_id)
      db.session.delete(venue)
      db.session.commit()
      flash(f'Venue (id: {venue_id}) was deleted successfully.')
    except Exception as err:
      db.session.rollback()
      flash(f'An error has occurred. Venue (id: {venue_id}) could not be deleted. Please try again.')
    finally:
      db.session.close()
    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists_query = Artist.query.order_by(Artist.name).all() 
    if not artists_query:
      abort(404)
    else:
      artists = artists_query
    return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    artist_search_term = request.form.get('search_term', '')
    artist_search_query = db.session.query(Artist).filter(Artist.name.ilike(f'%{artist_search_term}%')).all()
    results_list = []

    for artist_result in artist_search_query:
      results_list.append({
        'id': artist_result.id,
        'name': artist_result.name,
        'num_upcoming_shows': len(db.session.query(Show).filter(Show.artist_id == artist_result.id).filter(Show.start_time > datetime.now()).all())
      })

    artist_search_results_data = {
      'count': len(artist_search_query),
      'data': results_list
    }
    return render_template('pages/search_artists.html', results=artist_search_results_data, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist_query =  Artist.query.filter(Artist.id == artist_id).first()
    if not artist_query:
        abort(404)
    else:
      artist = artist_query
      
    past_shows_list = [] 
    past_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()

    for show in past_shows_query:
      past_shows_list.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "artist_image_link": show.venue.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })

    upcoming_shows_list = []
    upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()

    for show in upcoming_shows_query:
      upcoming_shows_list.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "artist_image_link": show.venue.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })
    
    artist_view_data = {
      "id": artist.id,
      "name": artist.name,
      "genres": artist.genres,
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website": artist.website,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "past_shows": past_shows_list,
      "upcoming_shows": upcoming_shows_list,
      "past_shows_count": len(past_shows_list),
      "upcoming_shows_count": len(upcoming_shows_list),
    }
    return render_template('pages/show_artist.html', artist=artist_view_data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist_query = Artist.query.get(artist_id)
    if not artist_query:
        abort(404)
    else: 
        artist = artist_query
    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # artist record with ID <artist_id> using the new attributes
    artist_query = Artist.query.get(artist_id)

    if not artist_query:
      flash('An error occurred. Please try again')
      print('An error occurred. Please try again: ', artist_query)
    else: 
      artist = artist_query

    try: 
      artist.name = request.form['name']
      artist.city = request.form['city']
      artist.state = request.form['state']
      artist.phone = request.form['phone']
      artist.genres = request.form.getlist('genres')
      artist.image_link = request.form['image_link']
      artist.facebook_link = request.form['facebook_link']
      artist.website = request.form['website_link']
      artist.seeking_venue = True if 'seeking_venue' in request.form else False 
      artist.seeking_description = request.form['seeking_description']
      db.session.commit()
      flash('Artist update was successful!')
    except Exception as err: 
      db.session.rollback()
      print(err)
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be edited.')
    finally: 
      db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue_query = Venue.query.get(venue_id)

    if not venue_query:
      abort(404)
    else: 
      venue = venue_query
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # UPDATE the venue record with ID <venue_id> using the new attributes
    venue_query = Venue.query.get(venue_id)

    if not venue_query:
      flash('An error occurred while updating. Please try again')
      print('An error occurred editing this venue: ', venue_query)
    else: 
      venue = venue_query

    try: 
      venue.name = request.form['name']
      venue.city = request.form['city']
      venue.state = request.form['state']
      venue.phone = request.form['phone']
      venue.genres = request.form.getlist('genres')
      venue.image_link = request.form['image_link']
      venue.facebook_link = request.form['facebook_link']
      venue.website = request.form['website_link']
      venue.seeking_venue = True if 'seeking_venue' in request.form else False 
      venue.seeking_description = request.form['seeking_description']
      db.session.commit()
      flash('Venue update was successful!')
    except Exception as err: 
      db.session.rollback()
      print(err)
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be edited.')
    finally: 
      db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    try: 
        artist = Artist(
          name = request.form['name'],
          city = request.form['city'],
          state = request.form['state'],
          phone = request.form['phone'],
          genres = request.form.getlist('genres'),
          facebook_link = request.form['facebook_link'],
          image_link = request.form['image_link'],
          website = request.form['website_link'],
          seeking_venue = True if 'seeking_venue' in request.form else False,
          seeking_description = request.form['seeking_description']
        )
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully created')
    except Exception as err:
        print(err)
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.. Please try again.')
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    shows_query = db.session.query(Show).join(Artist).join(Venue).all()
    if not shows_query:
        abort(404)
    else: 
        shows = shows_query

    shows_view_data = []
    for show in shows:
        shows_view_data.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })
    return render_template('pages/shows.html', shows=shows_view_data)

@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    try:
        show = Show(
          artist_id = request.form['artist_id'],
          venue_id = request.form['venue_id'],
          start_time = request.form['start_time'],
        )
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except Exception as err:
        db.session.rollback()
        print(err)
        flash('An error occurred. Artist could not be listed.Please try again.')
    finally:
        db.session.close()
    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
