import numpy as np
import pandas as pd
from requests import get
from bs4 import BeautifulSoup
import re
import time

#Since there are only 4 overall genres, I will manually grab those urls.
genres = [{
            'genre': 'Horror',
            'url' : 'https://www.barnesandnoble.com/b/books/fiction/horror/_/N-29Z8q8Z1d51'
          },
          {
            'genre': 'Romance',
            'url': 'https://www.barnesandnoble.com/b/books/romance/_/N-29Z8q8Z17y3'
          },
          {
              'genre': 'Mystery and Crime',
              'url' : 'https://www.barnesandnoble.com/b/books/mystery-crime/_/N-29Z8q8Z16g4'
          },
          {
              'genre': 'Sci-Fi and Fantasy',
              'url': 'https://www.barnesandnoble.com/b/books/science-fiction-fantasy/_/N-29Z8q8Z180l'
          }]

def get_sub_genre_urls(genre_list = genres):
    """
    This function takes in a list of dictionaries containing urls for the Horror, Romance, Mystery and Crime, and Sci-fi and Fantasy genres
    at barnesandnoble.com. Each dictionary also has the name of the genre for the link. 
    It then loops through each of them, web scrapes the urls for each
    sub genre, and finally returns a list of those urls.
    """
    #Create empty list to contain genre name and sub-genre url dicts
    sub_genres = []
    
    #Loop through each url in the genre_list
    for genre in genre_list:
        #Get the web content of the main genre
        response = get(genre['url'], headers = {'user-agent': 'Codeup DS Germain'})
        
        #Check status code, print message
        if response.status_code == 200:
            print(f'Response status code: {response.status_code}. The {genre["genre"]} genre is good to go.')
        else:
            print(f'Response status code: {response.status_code}. Something went wrong with the {genre["genre"]} genre!')
            
        #Parse the response
        soup = BeautifulSoup(response.content, 'html.parser')
        
        #Find the list of sub-genres
        sub_genre_list = soup.find('ul', id = 'sidebar-section-0')
        
        #Now find all the anchor tags that contain the urls for each sub-genre
        links = sub_genre_list.find_all('a')
        
        #Loop through each item in the links list
        for link in links:
            #Build the complete link
            complete_link = 'https://www.barnesandnoble.com' + link.attrs['href']

            #Everything after the semicolon in the url is not needed. Remove it
            complete_link = re.sub(r';.*', '', complete_link)

            #Build the dict to store the data
            temp_dict = {'genre': genre['genre'],
                         'sub-genre': complete_link.split('/')[-3],
                         'url': complete_link }
            
            #Append the new link to the list
            sub_genres.append(temp_dict)
            
    return sub_genres



def get_last_page(soup):
    """
    This function takes in the content of an html page. It should be the first page for 
    any sub-genre. It will find and return the number corresponding to the last page 
    available for the sub-genre.
    """
    #Now, find out how many pages there are in the sub-genre
    page_list = soup.find('ul', class_ = 'pagination search-pagination')

    #Now gather the anchor tags in the list
    a_tags = page_list.find_all('a')
    
    #Since the last anchor tag is for the very next page,
    #Select the second to last anchor tag. It will have the number associated with 
    #the last page in the sub-genre
    last_page = int(a_tags[-2].text.split('\n')[2])
    
    return last_page


def get_book_urls(sub_genres):
    """
    This function takes in a dictionary of sub-genre urls. It will loop through each of them
    and gather the individual book urls from all available pages in the sub-genre.
    It will return a list of dictionaries, with each dictionary containing the book's 
    overall genre and the individual book's url.
    """
    #First create an empty list to hold the book dictionaries
    book_urls = []
    
    #Now loop through each sub-genre
    for sub_genre in sub_genres:
        #Get the initial page for the sub-genre
        response = get(sub_genre['url'], headers = {'user-agent':'Codeup DS Germain'})
        
        #Check response
        if response.status_code == 200:
            print(f'Got first page of sub-genre: {sub_genre["genre"]}, {sub_genre["sub-genre"]}')
        else:
            print(f'Something went wrong at {sub_genre["genre"]}, {sub_genre["sub-genre"]}. Status code: {response.status_code}')
        
        #Parse it 
        soup = BeautifulSoup(response.content, 'html.parser')
        
        #Get the number corresponding to the last available page for the sub-genre
        last_page = get_last_page(soup)
        
        #Now increment through the pages
        for i in range(2, last_page + 1):
            
            #Scrape all book urls on the current page
            #Grab the section that contains all of the books on the page
            book_container = soup.find('div', class_ = 'product-shelf-grid')
            
            #Now get all the links for each book
            book_anchors = book_container.find_all('a', class_ = 'pImageLink')
    
            #Loop through each item in the links list
            for anchor in book_anchors:
                #Build the complete link
                complete_link = 'https://www.barnesandnoble.com' + anchor.attrs['href']

                #Everything after the semicolon in the url is not needed. Remove it
                complete_link = re.sub(r';.*', '', complete_link)

                #Create a temp_dict to store info
                temp_dict = {'genre': sub_genre['genre'],
                             'sub-genre': sub_genre['sub-genre'],
                             'url': complete_link}

                #Append the new link to the list
                book_urls.append(temp_dict)
                
            #Now create the url for the next page
            #I believe Nrpp stands for Num results per page, so we can change that if we want
            next_page = sub_genre['url'] + '?Nrpp=20&page=' + str(i)
            
            #Now get the content of the next page
            response = get(next_page, headers = {'user-agent': 'Codeup DS Germain'})
            
            #Check the response code again
            if response.status_code == 200:
                print(f'Acquired page {i} of {last_page} pages.')
            else:
                print(f'Something went wrong at page {i} of {last_page} pages! Status Code: {response.status_code}')
            
            #Now parse and update the soup variable for the next loop iteration
            soup = BeautifulSoup(response.content, 'html.parser')
            
    return book_urls


def get_book_blurbs(book_urls):
    """
    This function takes in a list of dictionaries that contain a book's overall genre, its sub-genre,
    and its unique url. This function will loop through each url in the given list of dictionaries,
    and scrape the description of each book. It will finally return a new list of dictionaries with 
    the books' descriptions included. It will also keep track of how long the function runs.
    """
    #Start the timer
    time_start = time.perf_counter()
    
    #Create a variable to keep track of the number of books that didn't have a blurb
    books_skipped = 0
    
    #Create a variable to keep track of the number of books that have been processed
    book_number = 0
    
    #Create the empty list to store the dictionaries
    book_blurbs = []
    
    #Now loop through each book url in the 'book_urls'
    for book in book_urls:
        #Update book_number
        book_number += 1
        
        #Every 100 entries, leave a progress message
        if book_number % 100 == 0:
            print(f'Total Entries So Far: {book_number}')
            print(f'Total Entries Left: {len(book_urls) - book_number}')
            print(f'Total Time So Far: { (time.perf_counter() - time_start) / 60} minutes\n')
        
        #Get the page content
        response = get(book['url'], headers = {'user-agent': 'Codeup DS Germain'})
        
        #Check the status code. If there is a problem, leave a message
        if response.status_code != 200:
            print(f'Something went wrong at book url #{book_number}! Status Code: {response.status_code}')
            print(f'Genre, Subgenre: {book["genre"]}, {book["sub-genre"]}')
            print(f'Book URL: {book["url"]}')
            continue
        
        #parse it
        soup = BeautifulSoup(response.content, 'html.parser')
        
        #Get the description
        blurb = soup.find('div', itemprop = 'description')
        
        #For testing
        #print(f"Current URL: {book['url']}")
        #print(f"Number: {book_number}")
        
        #Check that the description exists. If it does,
        #Remove leading and trailing whitespace and '\xa0'
        #Otherwise, continue the loop
        if blurb != None:
            blurb = blurb.text.strip().replace('\xa0 ', '')
        else:
            books_skipped += 1
            print(f"Book Skipped! URL: {book['url']}")
            print(f"Book Number: {book_number}\n")
            continue
        
        #Create temp dict
        temp_dict = {'genre': book['genre'],
                     'sub-genre': book['sub-genre'],
                     'blurb': blurb
                    }
        
        #Append the temp_dict to the book_blurbs list
        book_blurbs.append(temp_dict)
        
        #For testing
        #print(f'Book Number #{book_number} Complete.')
        
    #Inform the user that the function is done. Provide total time
    print(f'Function Complete! Total Time: { (time.perf_counter() - time_start) / 60 / 60} hours')
    print(f'Total Books Skipped: {books_skipped}')
    
    return book_blurbs

def acquire_data(genre_list = genres):
    """
    This function puts all of the above functions together and allows the user to gather all of the data with just one function call.

    Parameters:
        genre_list: The initial list of overall genre URL's.

    Returns:
        A dataframe containing each book's genre, sub-genre, and original description.
    """

    #Get all sub-genre URLs
    sub_genres = get_sub_genre_urls(genre_list)

    #Get all book URLs for each sub-genre
    book_urls = get_book_urls(sub_genres)

    #Convert to data frame
    url_df = pd.DataFrame(book_urls)

    #Drop duplicate entries
    url_df = url_df.drop_duplicates(subset = ['url'])

    #Now create separate dfs for each genre
    horror_df = book_urls[url_df.genre == 'Horror']
    romance_df = book_urls[url_df.genre == 'Romance']
    mystery_df = book_urls[url_df.genre == 'Mystery and Crime']
    fantasy_df = book_urls[url_df.genre == 'Sci-Fi and Fantasy']

    #Convert to a dict for ease of use in the function
    horror_urls = horror_df.to_dict('records')
    romance_urls = romance_df.to_dict('records')
    mystery_urls = mystery_df.to_dict('records')
    fantasy_urls = fantasy_df.to_dict('records')

    #Now retrieve all the individual book blurbs
    #Since doing them all at the same time is proving to be difficult,
    #Set up a series of function calls to get the blurbs one overall genre at a time

    #For the Horror Section:
    horror_blurbs = get_book_blurbs(horror_urls)

    #For the romance section
    romance_blurbs = get_book_blurbs(romance_urls)

    #For the mystery and crime section
    mystery_blurbs = get_book_blurbs(mystery_urls)

    #Before continuing, remove a certain entry from the mystery section that was giving me trouble.
    mystery_blurbs = mystery_blurbs.drop(mystery_blurbs.index[558])

    #For the Sci-Fi and Fantasy section
    fantasy_blurbs = get_book_blurbs(fantasy_urls)

    #Now that all the data has been acquired, create a new list to hold all entries
    book_blurbs = []

    #Now extend book_blurbs with all the data
    book_blurbs.extend(horror_blurbs)
    book_blurbs.extend(romance_blurbs)
    book_blurbs.extend(mystery_blurbs)
    book_blurbs.extend(fantasy_blurbs)

    #Now that the data is all in one list, convert it to a df
    book_blurbs = pd.DataFrame(book_blurbs)

    return book_blurbs