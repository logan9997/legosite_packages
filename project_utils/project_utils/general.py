import math
import os
import time

from config.config import PAGE_NUM_LIMIT, MISC_VIEWS, URL_REMOVE_CHARS


def timer(func):
    def inner(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        finish = round(time.time() - start, 5)
        print(f'\n<{func.__name__.upper()}> finished in {finish} seconds.\n')
        return result
    return inner


class General():

    def __init__(self) -> None:
        pass

    def get_base_url(self, request) -> str:
        return request.get_host().strip(' ')

    def get_previous_url(self, request) -> str:
        previous_url:str = request.META.get('HTTP_REFERER', '')

        if previous_url == '':
            return ''

        if '://' in previous_url:
            previous_url = previous_url.split('://')[1]

        previous_url = previous_url[previous_url.index('/'):]

        if '?' in previous_url:
            return previous_url.split('?')[0]
        return previous_url
    
    def get_filters_query_string(self, request, params):

        print('PARAMS',params)
        if 'metric_filters' in params:
            params.remove('metric_filters')

        query_string = '&'.join([
            f'{param}={request.session.get(param)}'
            for param in params if request.session.get(param) not in 
            [None, '', -1, '-1']
        ])

        #add metric filters to query string
        metric_limits = '&'.join([
            f'{metric}={value}' for metric, value in 
            request.session.get('metric_filters', {}).items() if 
            value not in [-1, '-1', None, '']
        ])

        query_string = query_string + '&' + metric_limits
        query_string = self.remove_chars_from_string(query_string, URL_REMOVE_CHARS)
        return query_string

    def get_sorts_and_pages_query_string(self, request, params):
        query_string = '&'.join([
            f'{param}={request.session.get(param)}'
            for param in params if request.session.get(param) != None
        ])

        query_string = self.remove_chars_from_string(query_string, URL_REMOVE_CHARS)
        return query_string
    
    def get_full_query_string(self, request, filters_params, sorts_and_pages_params):

        query_string = self.get_filters_query_string(request, filters_params)
        query_string = (
            query_string + '&' + 
            self.get_sorts_and_pages_query_string(request, sorts_and_pages_params)
        )
                
        if '?&' in query_string:
            query_string = query_string.replace('?&', '?')
        if '&&' in query_string:
            query_string = query_string.replace('&&', '&')
        return query_string
    
    def remove_chars_from_string(self, string:str, chars:list[str]) -> str:
        for char in chars:
            if char in string:
                string = string.replace(char, '')
        return string

    def check_slider_range(self, value: int, _list: list):
        if value >= len(_list) - 1:
            value = len(_list) - 1
        if value <= 0:
            value = 0
        return value

    def configure_relative_file_path(self, file_name: str, max_depth: int) -> str:
        path = file_name
        while True:
            if os.path.exists(path):
                return path
            path = '../' + path

            if path.count('../') >= max_depth:
                raise Exception(f'File {file_name} not found')

    def clean_html_codes(self, string: str):
        codes = {
            '&#41;': ')',
            '&#40;': '(',
            '&#39;': "'"
        }

        for k, v in codes.items():
            if k in string:
                string = string.replace(k, v)
        return string
    
    def check_if_page_not_int(self, current_page):
        try:
            current_page = int(current_page)
        except:
            current_page = 1
        return current_page

    def split_capitalize(self, string: str, split_value: str):
        return ' '.join(
            list(map(str.capitalize, string.split(split_value)))
        )

    def sort_items(self, items: list, sort: str, **order) -> list[dict]:
        sort_field = sort.split('-')[0]
        order = {'asc': False, 'desc': True}[sort.split('-')[1]]
        items = sorted(
            items, key=lambda field: field[sort_field], reverse=order)
        return items

    def sort_dropdown_options(self, options: list[dict[str, str]], field: str) -> list[dict[str, str]]:
        # loop through all options. If options['value'] matches to desired sort field, assign to variable
        selected_field = [
            option for option in options if option['value'] == field]

        # default, if code above fails
        if selected_field == []:
            print('\n\nFAILS - <sort_dropdown_options>\n\n')
            selected_field = options[0]
        else:
            selected_field = selected_field[0]

        # push selected element to front of list, remove its old position
        options.insert(0, options.pop(options.index(selected_field)))

        return options

    def check_page_boundaries(self, current_page: int, list_len: int, items_per_page: int) -> int:
        try:
            current_page = int(current_page)
        except:
            return 1

        conditions = [
            current_page <= math.ceil(list_len / items_per_page),
            current_page > 0,
        ]

        if not all(conditions):
            return 1

        return current_page

    def slice_num_pages(self, list_len: int, current_page: int, items_per_page: int):
        num_pages = [i+1 for i in range((list_len // items_per_page) + 1)]
        last_page = num_pages[-1] - 1

        list_slice_start = current_page - (PAGE_NUM_LIMIT // 2)
        list_slice_end = current_page - (PAGE_NUM_LIMIT // 2) + PAGE_NUM_LIMIT

        if list_slice_end > len(num_pages):
            list_slice_end = len(num_pages) - 1
            list_slice_start = list_slice_end - PAGE_NUM_LIMIT
        if list_slice_start < 0:
            list_slice_end -= list_slice_start
            list_slice_start = 0

        num_pages = num_pages[list_slice_start:list_slice_end]

        # remove last page. if len(items) % != 0 by ITEMS_PER_PAGE -> blank page with no items
        if list_len % items_per_page == 0:
            num_pages.pop(-1)

        if 1 not in num_pages:
            num_pages.insert(0, 1)

        if last_page not in num_pages:
            num_pages.append(last_page)

        if 0 in num_pages:
            num_pages.remove(0)

        if len(num_pages) == 1:
            return []

        return num_pages
    
    def remove_unused_get_params(self, request, get_params):
        url = request.get_full_path()
        if '?' not in url:
            return request
        
        url = url.split('?')[1]
        params = url.split('&')

        GET_dict = request.GET.copy()
        for param in params:
            param_key = param.split('=')[0]
            if param_key not in get_params and param_key in GET_dict:
                del GET_dict[param_key]

        request.GET = GET_dict
        return request

    def save_get_params(self, request, params: list[str]):
        request = self.remove_unused_get_params(request, params)
        for param in params:
            if request.GET.get(param) != None:
                request.session[param] = request.GET.get(param)
        request.session.modified = True
        return request

    def clear_get_params(self, request, params: list[str]):
        for param in params:
            if param in request.session:
                del request.session[param]
        request.session.modified = True
        return request
    
    def get_current_url(self, request) -> str:
        current_url = request.path
        for view in MISC_VIEWS:
            if view in current_url:
                current_url = current_url.replace(view, '')
                break
        return current_url

    def process_sorts_and_pages(self, request, params: list[str]):
        current_url = self.get_current_url(request)
        previous_url = self.get_previous_url(request)

        previous_url = previous_url.replace('/', '') 
        current_url = current_url.replace('/', '')

        if current_url != previous_url:
            request = self.clear_get_params(request, params)
        request = self.save_get_params(request, params)
        request.session.modified = True
        return request
    
    def convert_items_decimal_to_float(self, items):
        #convert tuples to lists to change last item from decimal.Decimal to float 
        items = [list(item) for item in items]
        for item in items:
            item[-1] = float(item[-1])
        return items

    def large_number_commas(self, number: float) -> str:
        number = str(number)
        if '.' in number:
            num_int = number.split('.')[0]
            num_decimal = '.' + number.split('.')[1]
        else:
            num_int = number
            num_decimal = ''

        sections = []

        remainder = len(num_int) % 3
        if remainder != 0:
            sections.append(num_int[:remainder])
            num_int = num_int[remainder:]

        for i in range(len(num_int)):
            if (i % 3) == 0:
                sections.append(num_int[i:i+3])

        number = ','.join(sections)+num_decimal
        return number


    def get_login_error_message(self, form):
        error_html = str(form.errors)
        errors = list(filter(lambda x: x != '</ul>', error_html.split('</li>')))


        for error in errors:
            field = error.replace('<ul class="errorlist">', '')
            field = field.split('<li>')[1]
            if 'Enter a valid email address' in error:
                error_msg = 'Invalid Email'
                break

            elif 'Ensure this value has at most' in error:
                max_chars = error.split(
                    'Ensure this value has at most'
                )[1].split(' characters')[0]
                field = ' '.join([word.capitalize() for word in field.split('_')])
                error_msg = f'{field} has a maximum length of {max_chars} characters.'
                break
            else:
                error_msg = 'Please fill in all required fields (*)'
        return error_msg