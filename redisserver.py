import redis

redis_pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0, decode_responses=True)
redis_conn = redis.StrictRedis(connection_pool= redis_pool, decode_responses=True)
