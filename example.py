from pysocialgraph.social import Request

eric = Request('http://ericholscher.com')
eric.populate_structure()
jacob = Request('http://jacobian.org')
jacob.populate_structure()

if jacob.loves(eric):
    print "Can you feeeeel the love toooonight!"
if eric.loves(jacob):
    print "The peace the evening brings."
