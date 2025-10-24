from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random
import json
import re
import base64
from io import BytesIO
from PIL import Image
from datetime import datetime

class FacebookScraper:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.driver = None
        self.graphql_responses = []  # Store captured GraphQL responses

        pass
        
    def initialize_driver(self):
        """Initialize Chrome webdriver with GraphQL interception support via CDP"""
        options = webdriver.ChromeOptions()

        # CRITICAL: Enable performance logging for GraphQL interception
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

        # Enable Chrome DevTools Protocol (required for network interception)
        options.add_experimental_option('perfLoggingPrefs', {
            'enableNetwork': True,
            'enablePage': False,
        })

        # DISABLE ANNOYING POPUPS - This was blocking scrolling!
        options.add_argument('--disable-notifications')  # Disable notification popups
        options.add_argument('--disable-popup-blocking')  # Disable popup blocking
        options.add_experimental_option('prefs', {
            'credentials_enable_service': False,  # Disable password manager
            'profile.password_manager_enabled': False,  # Disable password save prompt
            'profile.default_content_setting_values.notifications': 2,  # Block notifications
        })

        # Anti-detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option("useAutomationExtension", False)

        # Additional stealth
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')

        # Run in background (headless mode)
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-first-run')
        options.add_argument('--disable-default-apps')

        # Random user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        ]
        options.add_argument(f'user-agent={random.choice(user_agents)}')

        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Enable Network domain via CDP for GraphQL interception
        try:
            self.driver.execute_cdp_cmd('Network.enable', {})
            self.driver.execute_cdp_cmd('Page.enable', {})
            pass
        except Exception as e:
            pass
        
    def simulate_human_typing(self, element, text):
        """Simulate human-like typing patterns (optimized for speed)"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.02, 0.08))
            if random.random() < 0.05:
                time.sleep(random.uniform(0.1, 0.2))
                
    def login(self):
        """Login to Facebook"""
        pass
        self.driver.get("https://www.facebook.com/login")
        time.sleep(random.uniform(1.5, 2.5))

        # Enter email
        pass
        email_input = WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        time.sleep(random.uniform(0.5, 1))
        self.simulate_human_typing(email_input, self.email)

        # Wait between email and password
        time.sleep(random.uniform(1, 2))

        # Enter password
        pass
        password_input = WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.NAME, "pass"))
        )
        time.sleep(random.uniform(0.5, 1))
        self.simulate_human_typing(password_input, self.password)

        # Wait before clicking login button
        time.sleep(random.uniform(1, 2))

        # Click login button
        login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        ActionChains(self.driver)\
            .move_to_element(login_button)\
            .pause(random.uniform(1, 2))\
            .click()\
            .perform()

        # Wait for login to process and page to load (reduced time)
        pass
        time.sleep(random.uniform(8, 12))
        
    def navigate_to_profile(self, profile_url):
        """Navigate to a specific Facebook profile"""
        pass
        self.driver.get(profile_url)
        time.sleep(random.uniform(2, 4))
        pass

    def slow_scroll(self, step=500):
        """Optimized human-like scrolling (faster)"""
        # Scroll in smaller increments for realism
        steps = random.randint(2, 3)
        step_size = step // steps

        for _ in range(steps):
            self.driver.execute_script(f"window.scrollBy(0, {step_size});")
            time.sleep(random.uniform(0.1, 0.3))

        # Random pause (mimics reading) - reduced
        time.sleep(random.uniform(0.5, 1.0))

    def capture_graphql_responses(self):
        """Capture GraphQL API responses from browser performance logs using CDP"""
        pass

        graphql_data = []

        try:
            # Get performance logs (contains all network activity)
            logs = self.driver.get_log('performance')

            for entry in logs:
                try:
                    log = json.loads(entry['message'])['message']

                    # Filter for Network response received events
                    if log['method'] == 'Network.responseReceived':
                        response = log['params']['response']
                        request_id = log['params']['requestId']
                        url = response.get('url', '')

                        # Check if this is a GraphQL API call
                        if '/api/graphql/' in url or 'graphql' in url.lower():
                            pass

                            # Try to get response body
                            try:
                                response_body = self.driver.execute_cdp_cmd(
                                    'Network.getResponseBody',
                                    {'requestId': request_id}
                                )

                                body = response_body.get('body', '')

                                # Try to parse as JSON
                                if body:
                                    # Handle multi-line JSON responses
                                    lines = body.strip().split('\n')
                                    parsed_responses = []

                                    for line in lines:
                                        if line.strip():
                                            try:
                                                parsed_json = json.loads(line)
                                                parsed_responses.append(parsed_json)
                                            except:
                                                pass

                                    if parsed_responses:
                                        graphql_data.append({
                                            'url': url,
                                            'request_id': request_id,
                                            'responses': parsed_responses,
                                            'timestamp': time.time()
                                        })
                                        pass

                            except Exception as e:
                                # Response body might not be available
                                pass

                except Exception as e:
                    continue

            pass
            self.graphql_responses = graphql_data
            return graphql_data

        except Exception as e:
            pass
            return []

    def parse_graphql_manually(self, graphql_data, num_posts=None):
        """Enhanced manual parser - extracts ALL posts from timeline + stream/defer segments, sorts by time, saves all, then selects top N"""
        pass

        if not graphql_data:
            pass
            return []

        organized_posts = []

        # STEP 1: Extract ALL posts from ALL responses
        for idx, response_data in enumerate(graphql_data, 1):
            try:
                pass

                for response in response_data.get('responses', []):
                    # METHOD 1: Check main data.node.timeline_list_feed_units.edges
                    data = response.get('data', {})

                    if data:
                        node = data.get('node')
                        if node:
                            timeline_units = node.get('timeline_list_feed_units', {})
                            edges = timeline_units.get('edges', [])

                            if edges:
                                pass
                                for edge in edges:
                                    post = edge.get('node', {})
                                    self._extract_post_data(post, organized_posts)

                    # METHOD 2: Check stream/defer segments with specific path structure
                    if 'label' in response and 'path' in response and response.get('label', '').startswith('ProfileCometTimelineFeed_user$stream'):
                        # This is a stream/defer segment
                        stream_data = response.get('data', {})
                        if 'node' in stream_data:
                            post = stream_data['node']
                            pass
                            self._extract_post_data(post, organized_posts)

            except Exception as e:
                pass
                continue

        pass

        # STEP 2: Sort posts by creation time (latest first)
        if organized_posts:
            pass
            # Sort by created_time, handling None values
            organized_posts.sort(key=lambda x: x.get('created_time') or '1970-01-01T00:00:00Z', reverse=True)
            pass

        # STEP 3: Skip saving all posts (only save user-selected file)
        pass

        # STEP 4: Select top N latest posts if requested
        if num_posts and len(organized_posts) > num_posts:
            pass
            selected_posts = organized_posts[:num_posts]
            pass
            return selected_posts

        return organized_posts

    def _extract_post_data(self, post, organized_posts):
        """Extract post data from a single post node and add to organized_posts list"""
        try:
            # Extract basic info
            post_id = post.get('post_id') or post.get('id')
            permalink = post.get('permalink_url')

            # Extract author
            author_name = None
            feedback = post.get('feedback', {})
            if 'owning_profile' in feedback:
                author_name = feedback['owning_profile'].get('name')

            # Extract post text from comet_sections
            post_text = self._extract_text_from_comet_sections(post.get('comet_sections', {}))

            # Extract engagement from deep UFI feedback path
            ufi_feedback = self._get_ufi_feedback(post)

            # Extract likes (reaction_count)
            likes = self._extract_number(ufi_feedback.get('reaction_count'))

            # Extract comments (from comments_count_summary_renderer)
            comments_renderer = ufi_feedback.get('comments_count_summary_renderer', {})
            comments_feedback = comments_renderer.get('feedback', {})

            # Try comment_rendering_instance.comments.total_count (CORRECT path)
            comment_instance = comments_feedback.get('comment_rendering_instance', {})
            comments_obj = comment_instance.get('comments', {})
            comments = self._extract_number(comments_obj.get('total_count'))

            # Fallback to other locations if not found
            if comments is None:
                comments = self._extract_number(comments_feedback.get('total_comment_count'))
            if comments is None:
                comments = self._extract_number(comments_renderer.get('count'))

            # Extract shares
            shares = self._extract_number(ufi_feedback.get('share_count'))

            # Extract media URLs from correct nested path
            media_urls = []
            attachments = post.get('attachments', [])
            for attachment in attachments:
                styles = attachment.get('styles', {})
                att_data = styles.get('attachment', {})

                # METHOD 1: Check for all_subattachments (albums/multiple images)
                all_subs = att_data.get('all_subattachments', {})
                nodes = all_subs.get('nodes', [])

                if nodes:
                    # Extract from nodes (album format)
                    for node in nodes:
                        media = node.get('media', {})
                        # Try multiple URI locations
                        uri = (media.get('image', {}).get('uri') or
                               media.get('photo_image', {}).get('uri') or
                               media.get('viewer_image', {}).get('uri'))
                        if uri:
                            media_urls.append(uri)
                else:
                    # METHOD 2: Single image in attachment.media
                    media = att_data.get('media', {})
                    if media:
                        # Try multiple URI locations for single images
                        uri = (media.get('photo_image', {}).get('uri') or
                               media.get('image', {}).get('uri') or
                               media.get('viewer_image', {}).get('uri'))
                        if uri:
                            media_urls.append(uri)

            # Extract created_time - check comet_sections.timestamp.story.creation_time
            created_time = None
            comet_sections = post.get('comet_sections', {})
            if isinstance(comet_sections, dict):
                timestamp_obj = comet_sections.get('timestamp', {})
                if isinstance(timestamp_obj, dict):
                    timestamp_story = timestamp_obj.get('story', {})
                    if isinstance(timestamp_story, dict):
                        created_time = timestamp_story.get('creation_time')

            # Fallback to post-level fields if not found
            if not created_time:
                created_time = post.get('creation_time')

            # Convert Unix timestamp to ISO 8601 format
            if created_time:
                try:
                    dt = datetime.fromtimestamp(created_time)
                    created_time = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                except:
                    created_time = None

            if post_text or post_id:
                # Extract detailed reaction breakdown
                reactions_breakdown = self._extract_reactions_breakdown(ufi_feedback)

                # Extract hashtags from text
                hashtags = self._extract_hashtags(post_text)

                # Determine post type
                post_type = self._determine_post_type(post, attachments)

                # Extract video specific data
                video_data = self._extract_video_data(attachments)

                # Extract page/profile information
                page_info = self._extract_page_info(post)

                # Check if sponsored
                is_sponsored = self._check_if_sponsored(post)

                # Build organized post with only fields that have actual data
                organized_post = {
                    # Basic post data (always present)
                    'url': permalink,
                    'post_id': post_id,
                    'user_url': f"https://www.facebook.com/{page_info.get('profile_handle', '')}" if page_info.get('profile_handle') else "https://www.facebook.com/",
                    'user_username_raw': author_name,
                    'content': post_text,
                    'date_posted': created_time,

                    # Engagement metrics (always present)
                    'num_comments': comments,
                    'num_shares': shares,
                    'num_likes_type': {'type': 'Like', 'num': likes} if likes else {'type': 'Like', 'num': 0},
                    'likes': likes,
                    'count_reactions_type': reactions_breakdown,

                    # Content analysis (always present)
                    'hashtags': hashtags,
                    'post_type': post_type,
                    'is_sponsored': is_sponsored,

                    # Media data (always present)
                    'attachments': self._format_attachments(attachments, video_data),
                    'media_urls': media_urls,

                    # Basic page info (always present)
                    'page_name': author_name,
                    'profile_id': page_info.get('profile_id'),
                    'page_url': f"https://www.facebook.com/{page_info.get('profile_handle', '')}" if page_info.get('profile_handle') else "https://www.facebook.com/",
                    'profile_handle': page_info.get('profile_handle', ''),
                    'page_is_verified': page_info.get('is_verified', False),

                    # Technical metadata (always present)
                    'shortcode': post_id,
                    'is_page': True,
                    'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),

                    # Legacy fields for compatibility (always present)
                    'permalink_url': permalink,
                    'created_time': created_time,
                    'author_name': author_name
                }

                # Add optional fields only if they exist in the data
                if video_data.get('view_count') is not None and video_data.get('view_count') > 0:
                    organized_post['video_view_count'] = video_data.get('view_count')

                # Page info fields - only add if actually present in raw data
                if page_info.get('followers') is not None:
                    organized_post['page_followers'] = page_info.get('followers')

                if page_info.get('category'):
                    organized_post['page_category'] = page_info.get('category')

                if page_info.get('intro'):
                    organized_post['page_intro'] = page_info.get('intro')

                if page_info.get('profile_picture'):
                    organized_post['page_logo'] = page_info.get('profile_picture')
                    organized_post['avatar_image_url'] = page_info.get('profile_picture')

                if page_info.get('cover_photo'):
                    organized_post['header_image'] = page_info.get('cover_photo')

                if page_info.get('website'):
                    organized_post['page_external_website'] = page_info.get('website')

                if page_info.get('email'):
                    organized_post['page_email'] = page_info.get('email')

                if page_info.get('creation_time'):
                    organized_post['page_creation_time'] = page_info.get('creation_time')
                organized_posts.append(organized_post)
                pass
                pass
                pass

        except Exception as e:
            pass
            pass

    def _extract_reactions_breakdown(self, ufi_feedback):
        """Extract detailed reaction breakdown (Like, Love, Haha, etc.)"""
        try:
            reactions = []

            # METHOD 1: Extract specific reaction types from top_reactions (from investigation)
            top_reactions = ufi_feedback.get('top_reactions', {})
            if isinstance(top_reactions, dict):
                edges = top_reactions.get('edges', [])
                for edge in edges:
                    if isinstance(edge, dict):
                        node = edge.get('node', {})
                        reaction_name = node.get('localized_name')
                        reaction_count = edge.get('reaction_count')

                        if reaction_name and reaction_count:
                            try:
                                count = int(reaction_count)
                                if count > 0:
                                    reactions.append({
                                        'type': reaction_name,
                                        'reaction_count': count
                                    })
                            except (ValueError, TypeError):
                                pass

            # METHOD 2: Look for reaction counts in various other locations
            if not reactions:
                reaction_count = ufi_feedback.get('reaction_count', {})
                if isinstance(reaction_count, dict):
                    for reaction_type, count in reaction_count.items():
                        if isinstance(count, (int, float)) and count > 0:
                            reactions.append({
                                'type': reaction_type.capitalize(),
                                'reaction_count': int(count)
                            })

            # METHOD 3: Fallback to basic total count as "Count" type
            if not reactions:
                total_count = self._extract_number(ufi_feedback.get('reaction_count'))
                if total_count and total_count > 0:
                    reactions.append({
                        'type': 'Count',
                        'reaction_count': total_count
                    })

            return reactions
        except:
            return []

    def _extract_hashtags(self, text):
        """Extract hashtags from post text"""
        if not text:
            return []

        hashtags = re.findall(r'#(\w+)', text)
        return [tag.lower() for tag in hashtags]

    def _determine_post_type(self, post, attachments):
        """Determine post type (Post, Reel, Video, etc.)"""
        try:
            # Check for video attachments
            for attachment in attachments:
                styles = attachment.get('styles', {})
                att_data = styles.get('attachment', {})
                media = att_data.get('media', {})

                # Check if it's a video
                if media.get('__typename') == 'Video':
                    # Check if it's a reel
                    if 'reel' in att_data.get('url', '').lower():
                        return 'Reel'
                    return 'Video'

            # Check if it has images
            if attachments:
                return 'Post'

            # Text only post
            return 'Post'
        except:
            return 'Post'

    def _extract_video_data(self, attachments):
        """Extract video-specific data"""
        video_data = {'view_count': 0, 'video_length': None, 'video_url': None}

        try:
            for attachment in attachments:
                styles = attachment.get('styles', {})
                att_data = styles.get('attachment', {})
                media = att_data.get('media', {})

                if media.get('__typename') == 'Video':
                    # Extract view count (fallback to 0 if not found)
                    video_data['view_count'] = self._extract_number(media.get('view_count', 0))

                    # Enhanced video duration extraction
                    duration = self._extract_video_duration(media)
                    if duration:
                        video_data['video_length'] = duration

                    # Enhanced video URL extraction
                    video_url = self._extract_video_url(media)
                    if video_url:
                        video_data['video_url'] = video_url

                    break
        except:
            pass

        return video_data

    def _extract_video_duration(self, media):
        """Extract video duration from various locations in media data"""
        try:
            # METHOD 1: Direct playable_duration (from investigation)
            duration = media.get('playable_duration')
            if duration:
                # Convert seconds to readable format
                if isinstance(duration, (int, float)):
                    if duration < 60:
                        return f"{int(duration)} seconds"
                    elif duration < 3600:
                        minutes = int(duration // 60)
                        seconds = int(duration % 60)
                        return f"{minutes}:{seconds:02d}"
                    else:
                        hours = int(duration // 3600)
                        minutes = int((duration % 3600) // 60)
                        seconds = int(duration % 60)
                        return f"{hours}:{minutes:02d}:{seconds:02d}"

            # METHOD 2: Other duration fields
            duration = media.get('playable_duration_in_ms')
            if duration:
                duration_sec = duration / 1000
                return f"{int(duration_sec)} seconds"

            # METHOD 3: Fallback duration fields
            duration = media.get('duration') or media.get('length_in_second')
            if duration:
                return f"{int(duration)} seconds"

        except:
            pass

        return None

    def _extract_video_url(self, media):
        """Extract video URL from various locations in media data"""
        try:
            # METHOD 1: From videoDeliveryResponseFragment (from investigation)
            delivery_response = media.get('videoDeliveryResponseFragment', {})
            if isinstance(delivery_response, dict):
                delivery_result = delivery_response.get('videoDeliveryResponseResult', {})
                if isinstance(delivery_result, dict):
                    # Get progressive URLs (most compatible)
                    progressive_urls = delivery_result.get('progressive_urls', [])
                    if progressive_urls:
                        for url_obj in progressive_urls:
                            if isinstance(url_obj, dict):
                                url = url_obj.get('progressive_url')
                                if url and '.mp4' in url:
                                    return url

            # METHOD 2: Direct playable URL fields
            video_url = (media.get('playable_url') or
                        media.get('browser_native_hd_url') or
                        media.get('browser_native_sd_url'))
            if video_url:
                return video_url

            # METHOD 3: Check nested video data
            video_delivery = media.get('videoDeliveryLegacyFields')
            if isinstance(video_delivery, dict):
                video_url = video_delivery.get('progressive_url')
                if video_url:
                    return video_url

        except:
            pass

        return None

    def _extract_page_info(self, post):
        """Extract page/profile information"""
        page_info = {}

        try:
            # Extract from owning_profile
            feedback = post.get('feedback', {})
            owning_profile = feedback.get('owning_profile', {})

            if owning_profile:
                page_info['profile_id'] = owning_profile.get('id')
                page_info['profile_handle'] = owning_profile.get('username') or owning_profile.get('url', '').split('/')[-1]

                # Enhanced verification detection
                page_info['is_verified'] = self._detect_verification(post, owning_profile)

                page_info['followers'] = self._extract_number(owning_profile.get('subscribers', {}).get('count'))
                page_info['category'] = owning_profile.get('category_name')
                page_info['intro'] = owning_profile.get('bio') or owning_profile.get('introduction')
                page_info['profile_picture'] = owning_profile.get('profile_picture', {}).get('uri')
                page_info['cover_photo'] = owning_profile.get('cover_photo', {}).get('photo', {}).get('image', {}).get('uri')
                page_info['website'] = owning_profile.get('website')
                page_info['email'] = owning_profile.get('contact_email')

                # Creation time
                creation_time = owning_profile.get('creation_time')
                if creation_time:
                    try:
                        dt = datetime.fromtimestamp(creation_time)
                        page_info['creation_time'] = dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                    except:
                        pass
        except:
            pass

        return page_info

    def _detect_verification(self, post, owning_profile):
        """Detect if page/profile is verified using multiple methods"""
        try:
            # METHOD 1: Look for CometFeedUserVerifiedBadgeStrategy
            comet_sections = post.get('comet_sections', {})
            if isinstance(comet_sections, dict):
                # Check context_layout for verification badge
                context_layout = comet_sections.get('context_layout', {})
                if isinstance(context_layout, dict):
                    story = context_layout.get('story', {})
                    if isinstance(story, dict):
                        comet_sections_inner = story.get('comet_sections', {})
                        if isinstance(comet_sections_inner, dict):
                            badge = comet_sections_inner.get('badge', {})
                            if isinstance(badge, dict):
                                typename = badge.get('__typename')
                                if typename == 'CometFeedUserVerifiedBadgeStrategy':
                                    return True

            # METHOD 2: Search for verification badge pattern anywhere in post data
            def search_for_verification(obj):
                """Recursively search for verification indicators"""
                if isinstance(obj, dict):
                    # Check for verification badge typename
                    if obj.get('__typename') == 'CometFeedUserVerifiedBadgeStrategy':
                        return True
                    # Check for verification-related fields
                    if 'badge' in obj:
                        badge = obj['badge']
                        if isinstance(badge, dict) and badge.get('__typename') == 'CometFeedUserVerifiedBadgeStrategy':
                            return True
                    # Recursively search nested objects
                    for value in obj.values():
                        if search_for_verification(value):
                            return True
                elif isinstance(obj, list):
                    # Search through list items
                    for item in obj:
                        if search_for_verification(item):
                            return True
                return False

            # Search the entire post for verification indicators
            if search_for_verification(post):
                return True

            # METHOD 3: Fallback to owning_profile (less reliable)
            return owning_profile.get('is_verified', False)

        except Exception as e:
            # Fallback to owning_profile verification
            return owning_profile.get('is_verified', False)

    def _check_if_sponsored(self, post):
        """Check if post is sponsored/promoted"""
        try:
            # Look for sponsored indicators
            sponsored_data = post.get('sponsored_data')
            if sponsored_data:
                return True

            # Check for promotion indicators
            comet_sections = post.get('comet_sections', {})
            if isinstance(comet_sections, dict):
                content = comet_sections.get('content', {})
                if content.get('__typename') == 'CometFeedStorySponsoredStrategy':
                    return True

            return False
        except:
            return False

    def _format_attachments(self, attachments, video_data):
        """Format attachments in the target structure"""
        formatted_attachments = []

        try:
            for attachment in attachments:
                styles = attachment.get('styles', {})
                att_data = styles.get('attachment', {})
                media = att_data.get('media', {})

                attachment_obj = {
                    'id': media.get('id'),
                    'type': 'Video' if media.get('__typename') == 'Video' else 'Photo',
                    'url': media.get('image', {}).get('uri') or media.get('photo_image', {}).get('uri')
                }

                # Add video-specific fields
                if attachment_obj['type'] == 'Video':
                    attachment_obj['video_length'] = video_data.get('video_length')
                    attachment_obj['video_url'] = video_data.get('video_url')
                    attachment_obj['attachment_url'] = att_data.get('url')
                else:
                    attachment_obj['video_url'] = None

                formatted_attachments.append(attachment_obj)
        except:
            pass

        return formatted_attachments

    def _extract_text_from_comet_sections(self, sections):
        """Recursively extract text from comet_sections (can be dict or list)"""
        if not sections:
            return None

        # Handle dict structure (new Facebook GraphQL format)
        if isinstance(sections, dict):
            # Check for message/text field at this level
            if 'message' in sections:
                msg = sections['message']
                if isinstance(msg, dict) and 'text' in msg:
                    return msg['text']
                elif isinstance(msg, str):
                    return msg

            # Recursively search all values in the dict
            for key, value in sections.items():
                if isinstance(value, (dict, list)):
                    result = self._extract_text_from_comet_sections(value)
                    if result:
                        return result

        # Handle list structure (older format)
        elif isinstance(sections, list):
            for section in sections:
                if isinstance(section, dict):
                    # Check for message/text field
                    if 'message' in section:
                        msg = section['message']
                        if isinstance(msg, dict) and 'text' in msg:
                            return msg['text']
                        elif isinstance(msg, str):
                            return msg

                    # Recursively search in nested structures
                    result = self._extract_text_from_comet_sections(section)
                    if result:
                        return result

        return None

    def _get_ufi_feedback(self, post):
        """Navigate deep path to get UFI (User Feedback Interface) engagement data"""
        try:
            # Navigate: comet_sections.feedback.story.story_ufi_container.story
            #          .feedback_context.feedback_target_with_context
            #          .comet_ufi_summary_and_actions_renderer.feedback
            return (post.get('comet_sections', {})
                       .get('feedback', {})
                       .get('story', {})
                       .get('story_ufi_container', {})
                       .get('story', {})
                       .get('feedback_context', {})
                       .get('feedback_target_with_context', {})
                       .get('comet_ufi_summary_and_actions_renderer', {})
                       .get('feedback', {}))
        except:
            return {}

    def _extract_number(self, value):
        """Extract number from various GraphQL formats"""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, dict):
            # Try common number fields
            for key in ['count', 'total_count', 'value']:
                if key in value:
                    return value[key]
        return None


    def save_graphql_raw(self, filename='graphql_raw_data.json'):
        """Save raw GraphQL responses to JSON file"""
        if not self.graphql_responses:
            pass
            
            return None

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.graphql_responses, f, indent=2, ensure_ascii=False)

        pass
        return filename

    def save_graphql_organized(self, organized_data, filename='graphql_organized_data.json'):
        """Save AI-organized post data to JSON file"""
        if not organized_data:
            pass
            return None

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(organized_data, f, indent=2, ensure_ascii=False)

        pass
        return filename

    def save_all_posts(self, all_posts_data, filename='all_posts_complete.json'):
        """Save ALL extracted posts to JSON file (before user selection)"""
        if not all_posts_data:
            pass
            return None

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_posts_data, f, indent=2, ensure_ascii=False)

        pass
        return filename

    def calculate_optimal_scrolls(self, desired_posts):
        """
        Calculate optimal number of scrolls based on desired posts

        Based on analysis: 8 scrolls = 9 posts (1.1 posts per scroll average)
        """
        # Base rate: posts per scroll (from analysis)
        posts_per_scroll = 1.1

        # Calculate basic scrolls needed
        basic_scrolls = desired_posts / posts_per_scroll

        # Add buffer for safety (20% extra)
        buffer_scrolls = basic_scrolls * 0.2

        # Round up and ensure minimum/maximum limits
        optimal_scrolls = max(1, min(15, round(basic_scrolls + buffer_scrolls)))

        return optimal_scrolls

    def scrape_posts_graphql(self, num_posts=1, output_filename='graphql_organized_data.json'):
        """
        NEW METHOD: Scrape posts using GraphQL API interception + manual parsing

        This replaces HTML scraping with reliable API data extraction:
        1. Navigate and scroll to trigger GraphQL calls
        2. Capture GraphQL API responses
        3. Use manual parser to organize ALL the data
        4. Sort posts by creation time (latest first)
        5. Select top N most recent posts
        6. Save both raw and organized files

        Args:
            num_posts: Number of latest posts to return (default: 1 for testing)
        """
        pass

        # Step 1: Wait longer for initial GraphQL calls that contain first posts
        pass
        time.sleep(7)  # Further increased wait time to ensure first posts load

        # Step 1.5: Capture initial GraphQL responses BEFORE scrolling
        pass
        initial_graphql = self.capture_graphql_responses()
        initial_post_count = len(initial_graphql) if initial_graphql else 0
        pass

        # If no initial responses, wait a bit more and try again
        if initial_post_count == 0:
            pass
            time.sleep(3)
            initial_graphql = self.capture_graphql_responses()
            initial_post_count = len(initial_graphql) if initial_graphql else 0
            pass

        # Step 2: Calculate optimal scrolls and scroll to trigger additional post-loading GraphQL calls
        scroll_count = self.calculate_optimal_scrolls(num_posts)
        pass
        pass
        pass
        for i in range(scroll_count):
            pass
            self.slow_scroll(step=150)  # Smaller steps for more thorough coverage
            time.sleep(1.5)  # Slightly longer wait between scrolls for GraphQL to trigger

        # Extra wait to capture all additional GraphQL responses (proportional to scrolls)
        wait_time = max(2, min(5, scroll_count * 0.4))  # Scale wait time with scroll count
        pass
        time.sleep(wait_time)

        # Step 3: Capture ALL GraphQL responses (including new ones from scrolling)
        pass
        graphql_data = self.capture_graphql_responses()

        if not graphql_data:
            pass
            return []

        # Step 4: Skip saving raw GraphQL data
        pass

        # Step 5: Parse GraphQL data using manual parser
        pass
        organized_posts = self.parse_graphql_manually(graphql_data, num_posts=num_posts)

        if not organized_posts:
            pass
            return []

        # Step 6: Save organized data to user-specified file
        pass
        self.save_graphql_organized(organized_posts, output_filename)

        pass

        return organized_posts

    # ========================================================================
    # LEGACY HTML SCRAPING METHODS REMOVED
    # Replaced by GraphQL API interception (scrape_posts_graphql)
    # ========================================================================

    def save_to_json(self, posts_data, filename=None):
        """Save scraped data to JSON file"""
        if filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"facebook_posts_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(posts_data, f, indent=2, ensure_ascii=False)

        pass
        return filename

    def print_posts(self, posts_data):
        """Print the scraped posts data"""
        pass

        for idx, post in enumerate(posts_data, start=1):
            pass
            # Handle None values properly
            post_text = post.get('post_text') or 'N/A'
            if post_text != 'N/A':
                post_text = post_text[:100] + "..." if len(post_text) > 100 else post_text

            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

def get_user_inputs():
    """Get user inputs for scraping configuration"""
    pass

    pass

    # Get email
    email = input("📧 Facebook Email: ").strip()
    if not email:
        pass
        return None, None, None, None

    # Get password
    password = input("🔒 Facebook Password: ").strip()
    if not password:
        pass
        return None, None, None, None

    # Get page URL
    page_url = input("🔗 Facebook Page/Profile URL: ").strip()
    if not page_url:
        pass
        return None, None, None, None

    # Validate URL
    if not ("facebook.com" in page_url and ("http://" in page_url or "https://" in page_url)):
        pass
        return None, None, None, None

    # Get number of posts
    while True:
        try:
            num_posts = int(input("📊 Number of posts to fetch: ").strip())
            if num_posts <= 0:
                pass
                continue
            break
        except ValueError:
            pass

    return email, password, page_url, num_posts

# Interactive usage
if __name__ == "__main__":
    """
    ═══════════════════════════════════════════════════════════════════
    GRAPHQL-POWERED FACEBOOK SCRAPER - INTERACTIVE MODE
    ═══════════════════════════════════════════════════════════════════
    """

    try:
        # Get user inputs
        email, password, page_url, num_posts = get_user_inputs()

        if not all([email, password, page_url, num_posts]):
            pass
            exit(1)

        pass

        # Initialize the scraper
        scraper = FacebookScraper(email, password)

        # Setup and login
        scraper.initialize_driver()
        scraper.login()

        # Navigate to user-specified profile/page
        scraper.navigate_to_profile(page_url)

        # Scrape using GraphQL interception
        pass

        posts_data = scraper.scrape_posts_graphql(num_posts=num_posts)

        # Display results
        if posts_data:
            scraper.print_posts(posts_data)

            # Save to timestamped file
            filename = scraper.save_to_json(posts_data)

            pass
        else:
            pass

    except KeyboardInterrupt:
        pass
    except Exception as e:
        pass
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        try:
            scraper.close()
        except:
            pass
        pass
