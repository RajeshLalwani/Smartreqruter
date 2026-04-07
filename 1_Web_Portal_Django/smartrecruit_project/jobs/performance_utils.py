"""
Performance optimization utilities
Pagination, caching, and query optimization helpers
"""

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.cache import cache
from functools import wraps
import hashlib
import json


def paginate_queryset(queryset, page_number, items_per_page=10):
    """
    Paginate a queryset with error handling
    Returns (page_obj, paginator)
    """
    paginator = Paginator(queryset, items_per_page)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        page_obj = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        page_obj = paginator.page(paginator.num_pages)
    
    return page_obj, paginator


def cache_view_result(timeout=300, key_prefix='view'):
    """
    Decorator to cache view results
    Usage: @cache_view_result(timeout=600, key_prefix='job_list')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Generate cache key from request path and query params
            cache_key_parts = [
                key_prefix,
                request.path,
                request.GET.urlencode(),
                str(request.user.id) if request.user.is_authenticated else 'anonymous'
            ]
            cache_key = hashlib.md5(
                '|'.join(cache_key_parts).encode()
            ).hexdigest()
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Call the view function
            result = view_func(request, *args, **kwargs)
            
            # Cache the result
            cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def optimize_queryset(queryset, select_related=None, prefetch_related=None):
    """
    Optimize queryset with select_related and prefetch_related
    """
    if select_related:
        queryset = queryset.select_related(*select_related)
    
    if prefetch_related:
        queryset = queryset.prefetch_related(*prefetch_related)
    
    return queryset


def get_page_range(paginator, current_page, num_pages_to_show=5):
    """
    Get a smart page range for pagination display
    Shows pages around the current page
    """
    total_pages = paginator.num_pages
    
    if total_pages <= num_pages_to_show:
        return range(1, total_pages + 1)
    
    # Calculate start and end
    half = num_pages_to_show // 2
    
    if current_page <= half:
        start = 1
        end = num_pages_to_show
    elif current_page >= total_pages - half:
        start = total_pages - num_pages_to_show + 1
        end = total_pages
    else:
        start = current_page - half
        end = current_page + half
    
    return range(start, end + 1)


def batch_process(queryset, batch_size=100, callback=None):
    """
    Process queryset in batches to avoid memory issues
    """
    total = queryset.count()
    processed = 0
    
    while processed < total:
        batch = queryset[processed:processed + batch_size]
        
        if callback:
            callback(batch)
        
        processed += batch_size
        
        # Yield progress
        yield {
            'processed': min(processed, total),
            'total': total,
            'percentage': (min(processed, total) / total) * 100
        }


def get_or_cache(cache_key, callable_func, timeout=300):
    """
    Get from cache or execute function and cache result
    """
    result = cache.get(cache_key)
    
    if result is None:
        result = callable_func()
        cache.set(cache_key, result, timeout)
    
    return result


class QueryOptimizer:
    """
    Helper class for optimizing common query patterns
    """
    
    @staticmethod
    def get_applications_with_relations(queryset):
        """
        Optimize application queryset with common relations
        """
        return queryset.select_related(
            'candidate',
            'candidate__user',
            'job',
            'job__recruiter'
        )
    
    @staticmethod
    def get_jobs_with_relations(queryset):
        """
        Optimize job queryset with common relations
        """
        return queryset.select_related(
            'recruiter'
        ).prefetch_related(
            'applications'
        )
    
    @staticmethod
    def get_interviews_with_relations(queryset):
        """
        Optimize interview queryset with common relations
        """
        return queryset.select_related(
            'application',
            'application__candidate',
            'application__job'
        )


def invalidate_cache_pattern(pattern):
    """
    Invalidate all cache keys matching a pattern
    Note: This requires Redis backend for pattern matching
    """
    try:
        from django.core.cache import cache
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern(pattern)
    except Exception:
        # Fallback: just clear all cache
        cache.clear()


# Common cache keys
CACHE_KEYS = {
    'job_list': 'job_list_{page}_{filters}',
    'candidate_list': 'candidate_list_{page}_{filters}',
    'analytics': 'analytics_{recruiter_id}_{date_range}',
    'recommendations': 'recommendations_{user_id}',
    'trending_jobs': 'trending_jobs_{days}',
}


def generate_cache_key(template, **kwargs):
    """
    Generate a cache key from template and parameters
    """
    return template.format(**kwargs)
